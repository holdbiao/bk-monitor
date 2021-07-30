const { resolve } = require('path')
const util = require('util')
const fs = require('fs')
const readFile = util.promisify(fs.readFile)
const writeFile = util.promisify(fs.writeFile)
const r = path => resolve(__dirname, path)
const translateJson = async () => {
  const chunk = await readFile(r('./translate-zh.json', 'utf8'))
  const data = JSON.parse(chunk)
  Object.keys(data).forEach((key) => {
    data[key] = ''
  })
  writeFile(r('./translate-en.json'), JSON.stringify(data), 'utf8')
}
translateJson()
