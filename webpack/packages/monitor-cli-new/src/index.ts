import program from 'commander'
import excuteTask from './utils/excute-task'
import devTask from './tasks/dev'
import buildTask from './tasks/build'
// eslint-disable-next-line import/prefer-default-export
export const run =  () => {
  program
    .command('dev')
    .option('-m, --mobile', 'enable mobile mode')
    .option('-e, --email', 'enable email mode')
    .description('develop with dev mode')
    .action(async (cmd) => {
      await excuteTask(devTask)({
        production: false,
        mobile: !!cmd.mobile,
        email: !!cmd.email
      })
    })

  program
    .command('build')
    .option('-m, --mobile', 'enable mobile mode')
    .option('-e, --email', 'enable email mode')
    .option('-a, --analyze', 'enable analyze mode')
    .description('build production mode')
    .action(async (cmd) => {
      await excuteTask(buildTask)({
        production: true,
        analyze: !!cmd.analyze,
        mobile: !!cmd.mobile,
        email: !!cmd.email
      })
    })

  program.on('command:*', () => {
    console.error('Invalid command: %s\nSee --help for a list of available commands.', program.args.join(' '))
    process.exit(1)
  })

  program.parse(process.argv)
}
