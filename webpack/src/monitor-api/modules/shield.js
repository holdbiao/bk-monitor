import { request } from '../base'

export const shieldList = request('POST', 'rest/v2/shield/shield_list/')
export const frontendShieldList = request('POST', 'rest/v2/shield/frontend_shield_list/')
export const shieldDetail = request('GET', 'rest/v2/shield/shield_detail/')
export const frontendShieldDetail = request('GET', 'rest/v2/shield/frontend_shield_detail/')
export const shieldSnapshot = request('POST', 'rest/v2/shield/shield_snapshot/')
export const addShield = request('POST', 'rest/v2/shield/add_shield/')
export const editShield = request('POST', 'rest/v2/shield/edit_shield/')
export const disableShield = request('POST', 'rest/v2/shield/disable_shield/')
export const updateFailureShieldContent = request('GET', 'rest/v2/shield/update_failure_shield_content/')

export default {
  shieldList,
  frontendShieldList,
  shieldDetail,
  frontendShieldDetail,
  shieldSnapshot,
  addShield,
  editShield,
  disableShield,
  updateFailureShieldContent
}
