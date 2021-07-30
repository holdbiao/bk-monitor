import { Task, TaskRunner } from '../typings/task'
import { bundleTask } from '../utils/bundle-task'
interface DevOption {
  mobile: boolean,
  production: boolean,
  email?: boolean,
}


const pluginDevRunner: TaskRunner<DevOption> = async (options: DevOption) => {
  process.env.NODE_ENV = 'development'
  await bundleTask(options)
}

export default new Task<DevOption>('dev', pluginDevRunner)
