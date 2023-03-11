import asyncio

import matplotlib

from package.analyzers.DayTime import DayTimeAnalyzer
from package.analyzers.Frequency import FrequencyAnalyzer
from package.analyzers.TotalCount import TotalCountAnalyzer
from package.analyzers.VoiceDuration import VoiceDurationAnalyzer
from package.analyzers.WordCount import WordCountAnalyzer
from package.cli.get_args import get_args
from package.logging import setup_loggers
from package.models import init_connection
from package.Reporter import Reporter

matplotlib.use('Agg')


# TODO: Manual language input or a more advanced technique to analyze the language
# TODO: Better tasks distribution and to look into gRCP or other bi-derectional data transfer protocol and a separate cli command
# TODO: Cache dataframe data in the filesystem
# TODO: Come up with a way how the word usage frequency data could be displayed or just cut down the number of words displayed in the bar graph
# TODO: Gather functionality into sub-command

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


async def main():
    setup_loggers()
    args = get_args()

    await init_connection()

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



if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    loop.run_until_complete(main())
