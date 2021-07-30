/* eslint-disable no-param-reassign */
const moduleFiles = require.context('./modules', false, /\.js$/)
const modules = moduleFiles.keys().reduce((modules, modulePath) => {
  const moduleName = modulePath.replace(/^\.\/(.*)\.\w+$/, '$1')
  const value = moduleFiles(modulePath)
  modules[moduleName] = value.default
  return modules
}, {})

export default modules
