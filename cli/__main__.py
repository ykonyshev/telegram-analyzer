import asyncio

from analysis.analyzers.DayTime import DayTimeAnalyzer
from analysis.analyzers.Frequency import FrequencyAnalyzer
from analysis.analyzers.TotalCount import TotalCountAnalyzer
from analysis.analyzers.VoiceDuration import VoiceDurationAnalyzer
from analysis.analyzers.WordCount import WordCountAnalyzer
from analysis.logging import setup_loggers
from analysis.models import init_connection
from analysis.Reporter import Reporter
from cli.get_args import get_args

# TODO: Better project structure is never spare. The modules are all over the place, to be honest
# TODO: Subcommands code separation, a more robust subcommands system
# TODO: Separate gather and report
# TODO: Config file param to load arbiturary configs and not only in the project file
# TODO: Make the generate run on commit.
# TODO: Cache dataframe data in the filesystem
# TODO: Come up with a way how the word usage frequency data could be displayed or just cut down the number of words displayed in the bar graph
# TODO: Generate models automatically from the telegram api schema

# & Later
# TODO: Implament more of the api in the orm (like users and sticketsets and so on)
# TODO: Support groups
# TODO: Decide which API is the most suitable. Whether to let the user choose when to run data collection or just run inside the context manager
# TODO: Make the script work with export files for both telegram chats as well as whatsapp

# * Graph ideas
# TODO: By user word usage frequency
# TODO: Total messages, words count to time
# TODO: Voice max message duration by day
# TODO: Sigle word frequency to time
# TODO: Average response time to time
# TODO: Reactions usage frequency and kind to time
# TODO: Average "thread" length to time?
# TODO: User message types.


_cleanup_coroutines = []


async def main() -> None:
    logger = setup_loggers()
    args = get_args()

    if args.action == 'report' or args.processing_action == 'server':
        await init_connection()

    match args.action:
        case 'report':
            async with Reporter(
                args.ids,
                args.graphs_output,
                args.media_folder,
                [
                    WordCountAnalyzer,
                    FrequencyAnalyzer,
                    DayTimeAnalyzer,
                    VoiceDurationAnalyzer,
                    TotalCountAnalyzer
                ],
                args.gather_limit,
                args.skip_gather
            ) as reporter:
                await reporter.generate_full_report()
                if len(args.ids) >= 1 and args.generate_individual:
                    await reporter.generate_individual()

        case 'processing':
            match args.processing_action:
                case 'server':
                    from processing.server import serve
                    server = await serve(
                        args.address
                    )

                    # TODO: Custom server to avoid this.
                    async def graceful_shutdown() -> None:
                        logger.info(f'Gracefully shutting down the server! Waiting for {args.grace_period}')
                        await server.stop(args.grace_period)

                    _cleanup_coroutines.append(graceful_shutdown())
                    await server.wait_for_termination()

                case 'client':
                    from processing.client import run
                    await run(
                        args.server_address,
                        args.model_name,
                        args.device_type,
                        args.threads,
                        args.model_root,
                        args.tasks_limit
                    )


if __name__ == "__main__":
    loop = asyncio.new_event_loop()

    try:
        loop.run_until_complete(main())
    finally:
        if len(_cleanup_coroutines) > 0:
            loop.run_until_complete(*_cleanup_coroutines)

        loop.close()
