import asyncio

import matplotlib

from package.analyzers.DayTime import DayTimeAnalyzer
from package.analyzers.Frequency import FrequencyAnalyzer
from package.analyzers.WordCount import WordCountAnalyzer
from package.cli.get_args import get_args
from package.config import config
from package.models import init_connection
from package.MyClient import MyClient
from package.Reporter import Reporter

matplotlib.use('Agg')

# TODO: Include the username of some other indentification infortaion in the output folder name
# TODO: Logging

async def main():
    args = get_args()

    await init_connection()
    client = MyClient('anon', config.telegram_api.id, config.telegram_api.hash)

    async with client:
        reporter = Reporter(args.ids, client, args.graphs_output)
        reporter.add_analyzer(WordCountAnalyzer, FrequencyAnalyzer, DayTimeAnalyzer)
        await reporter.gather_missing_messages()

        await reporter.generate_full_report()

        if args.generate_individual:
            await reporter.generate_individual()


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    loop.run_until_complete(main())
