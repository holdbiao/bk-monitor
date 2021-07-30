const util = require('util')
const execFile = util.promisify(require('child_process').exec)

const getExecShell = () => {
  switch (process.env.execMode) {
    case 'install':
      return 'sh webpack/npm-install-all.sh'
    case 'update':
      return 'sh webpack/npm-update.sh'
    case 'move':
      return 'sh webpack/move-build-file.sh'
    default :
      console.error('未获取execMode环境变量')
      process.exit(1)
  }
}

const execShellFiles = async () => {
  console.log(`execMode: ${process.env.execMode}`)
  const { stdout, stderr } = await execFile(getExecShell()).catch((err) => {
    console.log(`执行${process.env.execMode}出错了`)
    console.error(err)
    process.exit(1)
  })
  stdout && console.log(`stdout: ${stdout}`)
  stderr && console.log(`stderr: ${stderr}`)
  console.log('执行完成')
}
execShellFiles()
