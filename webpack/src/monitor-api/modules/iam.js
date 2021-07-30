import { request } from '../base'

export const getAuthorityMeta = request('GET', 'rest/v2/iam/get_authority_meta/')
export const checkAllowedByActionIds = request('POST', 'rest/v2/iam/check_allowed_by_action_ids/')
export const getAuthorityDetail = request('POST', 'rest/v2/iam/get_authority_detail/')
export const test = request('GET', 'rest/v2/iam/test/')

export default {
  getAuthorityMeta,
  checkAllowedByActionIds,
  getAuthorityDetail,
  test
}
