import useSpinner from '../use-spinner'
import fastGlob from 'fast-glob'
import { resolve as resolvePath } from 'path'
import { CLIEngine } from 'eslint'
const getTypescriptSources = () => fastGlob(resolvePath(process.cwd(), 'src/**/*.+(ts|tsx)'))
export default useSpinner<{fix?: boolean}>('Linting', async ({ fix } = {}) => {
  const configFile = await fastGlob(resolvePath(
    process.cwd(),
    '.eslintrc?(.cjs|.js|.json|.yaml|.yml)'
  )).then((filePaths) => {
    if (filePaths.length > 0) {
      return filePaths[0]
    }
    return resolvePath(__dirname, '../../../config/bluking-eslint.json')
  })

  const cli = new CLIEngine({
    configFile,
    fix
  })

  const report = cli.executeOnFiles(await getTypescriptSources())

  if (fix) {
    CLIEngine.outputFixes(report)
  }

  const { errorCount, results, warningCount } = report

  if (errorCount > 0 || warningCount > 0) {
    const formatter = cli.getFormatter()
    console.log('\n')
    console.log(formatter(results))
    console.log('\n')
    throw new Error(`${errorCount + warningCount} linting errors found in ${results.length} files`)
  }
})
