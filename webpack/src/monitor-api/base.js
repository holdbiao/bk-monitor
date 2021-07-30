/* eslint-disable no-param-reassign */
/* eslint-disable import/prefer-default-export */
import axios from './axios/axios'
import { CancelToken } from 'axios'
import { bkMessage  } from './utils/index'
const defaultConfig = { needBiz: true,
  needRes: false,
  isAsync: false,
  needMessage: true,
  cancelToken: null,
  needCancel: false,
  cancelFn(c) {},
  onUploadProgress(e) {}
}
const noMessageCode = [3308005, 3314003, 3314004] // 无数据状态下 不弹窗
export const request = function (method, url) {
  return function (id, params, config = {}) {
    let newUrl = url
    let data = {}
    if (typeof id === 'number' || typeof id === 'string') {
      newUrl = url.replace('{pk}', id)
      data = params || {}
      config = Object.assign({}, defaultConfig, config || {})
    } else {
      data = id || {}
      config = Object.assign({}, defaultConfig, params || {})
    }
    const methodType = method.toLocaleLowerCase() || 'get'
    if (config.isAsync) {
      config.headers = {
        'X-Async-Task': true
      }
    }
    // needCancel用于配置是否需要设置取消请求 如果设置true有两种方式设置 1、设置外部传递过来的cancelFn 2、设置自定义的CancelToken
    if (config.needCancel && !config.cancelToken) {
      config.cancelToken = new CancelToken(config.cancelFn)
    }
    if (methodType === 'get') {
      if (!Object.prototype.hasOwnProperty.call(data, 'bk_biz_id')) {
        data.bk_biz_id = window.cc_biz_id
      }
      return axios({
        method: 'get',
        url: newUrl,
        params: data,
        needMessage: false,
        ...config
      }).then((res) => {
        if (config.needRes) {
          return Promise.resolve(res)
        }
        return Promise.resolve(res.data)
      })
        .catch((err) => {
          if (config.needMessage) {
            err.message && bkMessage(err.message)
          }
          return Promise.reject(err)
        })
    }
    Object.keys(data).forEach((key) => {
      const type = String(data[key])
      if (type === '[object FileList]' || type === '[object File]') {
        const formData = new FormData()
        Object.keys(data).forEach((key) => {
          formData.append(key, data[key])
        })
        data = formData
        config.headers = {
          'content-type': 'multipart/form-data',
          productionTip: true
        }
      }
    })
    if (config.needBiz && !Object.prototype.hasOwnProperty.call(data, 'bk_biz_id')) {
      if (data instanceof FormData) {
        data.append('bk_biz_id', window.cc_biz_id)
      } else {
        data.bk_biz_id = window.cc_biz_id
      }
    }
    return axios({
      method,
      url: newUrl,
      data,
      ...config
    }).then((res) => {
      if (config.needRes) {
        return Promise.resolve(res)
      }
      return Promise.resolve(res.data)
    })
      .catch((err) => {
        if (config.needMessage && !noMessageCode.includes(err.code)) {
          err.message && bkMessage(err.message)
        }
        return Promise.reject(err)
      })
  }
}
