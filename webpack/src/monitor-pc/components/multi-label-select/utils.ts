import { IList, ITreeItem } from './types'

/**
 * 标签数组转树形结构
 * @param list 标签接口数据
 */
export const labelListToTreeData = (list: IList[]): ITreeItem[] => {
  const localList = []
  const infoMap = list.reduce((map, node) => {
    const parentKey = getParentKey(node.labelName)
    const item = {
      name: getNodeName(node.labelName),
      id: node.id,
      key: node.labelName,
      parentKey
    }
    localList.push(item)
    map[item.key] = item
    return map
  }, {})
  return localList.filter((node) => {
    const { parentKey } = node
    if (infoMap[parentKey]) {
      const temp = infoMap[parentKey]
      temp.children ? temp.children.push(node) : temp.children = [node]
    }
    return !parentKey
  })
}

/**
 * @param str a/b
 * @param leng
 */
const getNodeName = (str: string, leng = 1) => {
  const res = str.split('/').filter(item => item)
  return res ? res[res.length - leng] : str
}

/**
 * @param str a/b
 */
const getParentKey = (str: string) => {
  const res = str.split('/').filter(item => item)
  return res?.length > 1 ? res.slice(0, res.length - 1).join('/') : null
}
