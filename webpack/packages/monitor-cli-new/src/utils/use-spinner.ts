import ora from 'ora'
type spinFn<T> = (options: T) => Promise<void>
export default <T = any>(label: string, cb: spinFn<T>, killProcess = true) => async (options: T) => {
  const spinner = ora(label)
  spinner.start()
  try {
    await cb(options)
    spinner.succeed()
  } catch (e) {
    console.trace(e)
    spinner.fail(e.message || e)
    if (killProcess) {
      process.exit(1)
    }
  }
}
