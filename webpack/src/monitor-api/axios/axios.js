/* eslint-disable no-param-reassign */
import axios from 'axios'
import qs from 'qs'
import { getCookie } from '../../monitor-common/utils/utils'
import { bkMessage, authorityStore } from '../utils/index'
// 错误请求处理 3314001(名称重复)
const noMessageCode = [3314001, 3310003]
const errorHandle = (response) => {
  switch (response.status) {
    case 400:
      if (!noMessageCode.includes(response.data.code)) {
        bkMessage(response.data.message || '请求出错了！')
      }
      break
    case 401:
      if (process.env.NODE_ENV === 'development') {
        window.location.href = `${process.env.loginUrl}?c_url=${process.env.devUrl}`
      } else {
        const handleLoginExpire = () => {
          window.location.href = `${window.bkPaasHost.replace(/\/$/g, '')}/login/`
        }
        const { data } = response
        // eslint-disable-next-line camelcase
        if (data?.has_plain) {
          try {
            window.LoginModal.$props.loginUrl = data.login_url
            window.LoginModal.show()
          } catch (_) {
            handleLoginExpire()
          }
        } else {
          handleLoginExpire()
        }
      }
      break
    case 404:
      bkMessage('请求的资源不存在')
      break
    case 403:
    case 499:
      authorityStore()?.showAuthorityDetail?.(response.data)
      break
    default:
      break
  }
}

const instance = axios.create({
  timeout: 1000 * 120,
  withCredentials: true,
  paramsSerializer(params) {
    return qs.stringify(params, { arrayFormat: 'brackets' })
  },
  baseURL: window.site_url,
  xsrfCookieName: 'X-CSRFToken'
})
instance.defaults.headers.post['Content-Type'] = 'application/x-www-form-urlencoded'

instance.interceptors.request.use(
  (config) => {
    if (!['HEAD', 'OPTIONS', 'TRACE'].includes(config.method.toUpperCase())) {
      config.headers['X-CSRFToken'] = getCookie(window.csrf_cookie_name)
    }
    config.headers['X-Requested-With'] = 'XMLHttpRequest'
    return config
  },
  error => Promise.error(error)
)
instance.interceptors.response.use(
  // 请求成功
  (res) => {
    if (!res.data.result) {
      return Promise.reject(res.data)
    }
    if (res.status === 200) {
      if (!res.data.result) {
        return Promise.reject(res.data)
      }
      return Promise.resolve(res.data)
    }
    return Promise.reject(res)
  },
  // 请求失败
  (error) => {
    const { response } = error
    if (response) {
      // 请求已发出，但是不在2xx的范围
      errorHandle(response)
      return Promise.reject(response)
    }
    // 处理断网的情况
    // eg:请求超时或断网时，更新state的network状态
    // network状态在app.vue中控制着一个全局的断网提示组件的显示隐藏
    // 关于断网组件中的刷新重新获取数据，会在断网组件中说明
    // if (!window.navigator.onLine) {
    //     store.commit('changeNetwork', false)
    // } else {
    // }
    return Promise.reject(error)
  }
)

export default instance
