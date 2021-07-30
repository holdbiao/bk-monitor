import { request } from '../base'

export const getUserInfo = request('GET', 'rest/v2/user_role/')
export const saveRolePermission = request('POST', 'rest/v2/user_role/')
export const listGlobalConfig = request('GET', 'rest/v2/global_config/')
export const setGlobalConfig = request('POST', 'rest/v2/global_config/')

export default {
  getUserInfo,
  saveRolePermission,
  listGlobalConfig,
  setGlobalConfig
}
