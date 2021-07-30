/*
 * @Author:
 * @Date: 2021-05-25 19:15:01
 * @LastEditTime: 2021-06-17 17:51:43
 * @LastEditors:
 * @Description:
 */
import moment from 'moment'
/**
 * 生成一个随机字符串ID
 * @param len 随机ID的长度 默认8位字符
 */
export const getRandomId = (len = 8): string => {
  const chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
  const charsLen = chars.length
  let id = ''
  for (let i = 0; i < len; i++) {
    id += chars.charAt(Math.floor(Math.random() * charsLen))
  }
  return id
}

/**
 * 数据检索日期范围转换
 * @param {*} timeRange number | string | array
 */
export const handleTimeRange  = (timeRange: number | string | string[]): { startTime: number, endTime: number } => {
  let startTime = null
  let endTime = null
  if (typeof timeRange === 'number') {
    endTime = moment().unix()
    startTime = endTime - (timeRange / 1000)
  } else {
    switch (timeRange) {
      case 'today': // 今天到现在为止
        startTime = moment().format('YYYY-MM-DD 00:00:00')
        endTime = moment().unix()
        break
      case 'yesterday': // 昨天
        startTime = moment().subtract(1, 'days')
          .format('YYYY-MM-DD 00:00:00')
        endTime = moment().subtract(1, 'days')
          .format('YYYY-MM-DD 23:59:59')
        break
      case 'beforeYesterday': // 前天
        startTime = moment().subtract(2, 'days')
          .format('YYYY-MM-DD 00:00:00')
        endTime = moment().subtract(2, 'days')
          .format('YYYY-MM-DD 23:59:59')
        break
      case 'thisWeek': // 本周一到现在为止
        startTime = moment().day('Monday')
          .format('YYYY-MM-DD 00:00:00')
        endTime = moment().unix()
        break
      default: // 自定义时间段
        if (typeof timeRange === 'string') {
          const timeArr = timeRange.split('--')
          startTime = timeArr[0].trim()
          endTime = timeArr[1].trim()
        } else {
          startTime = timeRange[0]
          endTime = timeRange[1]
        }
        break
    }
    endTime = typeof endTime === 'number' ? endTime : moment(endTime).unix()
    startTime = typeof startTime === 'number' ? startTime : moment(startTime).unix()
  }
  return {
    startTime,
    endTime
  }
}
/**
 * 下载文件
 * @param url 资源地址
 * @param name 资源名称
 */
export const downFile = (url: string, name = ''): void => {
  const element = document.createElement('a')
  element.setAttribute('href', url)
  element.setAttribute('download', name)
  element.style.display = 'none'
  document.body.appendChild(element)
  element.click()
  document.body.removeChild(element)
}
