import { Task, TaskRunner } from '../typings/task'
import { bundleTask } from '../utils/bundle-task'
interface PluginBuildOption {
  mobile: boolean;
  production: boolean;
  analyze?: boolean;
  email?: boolean;
}


const pluginBuildRunner: TaskRunner<PluginBuildOption> = async ({ mobile, production, analyze, email }) => {
  process.env.NODE_ENV = 'production'
  await bundleTask({ mobile, production, analyze, email })
}

export default new Task<PluginBuildOption>('build', pluginBuildRunner)
