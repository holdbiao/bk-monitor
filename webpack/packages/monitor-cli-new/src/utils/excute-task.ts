import chalk from 'chalk'
import { Task } from '../typings/task'

export default <T>(task: Task<T>) => async (options: T) => {
  console.log(chalk.yellow(`Running ${chalk.bold(task.name)} task`))
  task.setOptions(options)
  try {
    console.group()
    await task.exec()
    console.groupEnd()
  } catch (e) {
    console.trace(e)
    process.exit(1)
  }
}
