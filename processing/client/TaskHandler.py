import aiofiles
import whisper
from bson import ObjectId
from tqdm import tqdm
from whisper.decoding import DecodingResult

from analysis.utils.LoggerTimer import LoggerTimer
from processing.proto.tasks_pb2 import SubmitTaskRequest, Task


class TaskHandler:
    def __init__(
        self,
        model_name: str,
        model: whisper.Whisper,
        task: Task
    ) -> None:
        self.model_name = model_name
        self.model = model
        self.task = task


    async def _process_single(
        self,
        audio_file: bytes
    ) -> DecodingResult | list[DecodingResult]:
        async with aiofiles.tempfile.NamedTemporaryFile('wb') as handle:
            await handle.write(audio_file)

            audio = whisper.load_audio(str(handle.name))
            audio = whisper.pad_or_trim(audio)

            mel = whisper.log_mel_spectrogram(audio).to(self.model.device)

            options = whisper.DecodingOptions(
                language=self.task.audio_language,
                fp16=False
            )

            result = whisper.decode(self.model, mel, options)
            return result


    async def handle(
        self
    ) -> SubmitTaskRequest:
        task_id = ObjectId(self.task.id)
        results: list[SubmitTaskRequest.AudioContents] = []

        for details in tqdm(
            self.task.audio_files,
            desc=f'Processing audio for {task_id = }'
        ):
            with LoggerTimer(
                'took {:.2f}s to process {} seconds of audio',
                details.duration
            ):
                decoded = await self._process_single(
                    details.file_contents
                )

            decoding_results = decoded if isinstance(decoded, list) else [decoded]

            for single_result in decoding_results:
                results.append(SubmitTaskRequest.AudioContents(
                    document_id=details.document_id,
                    language=single_result.language,
                    text=single_result.text
                ))

        return SubmitTaskRequest(
            task_id=self.task.id,
            details=results,
            model_used=self.model_name
        )
