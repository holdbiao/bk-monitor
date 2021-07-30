import { request } from '../base'

export const phoneReceiver = request('GET', 'rest/v2/phone_receiver/')
export const memberData = request('GET', 'rest/v2/member_data/')
export const addMenu = request('POST', 'rest/v2/add_menu/')
export const editMenu = request('POST', 'rest/v2/edit_menu/')
export const deleteMenu = request('POST', 'rest/v2/delete_menu/')
export const listMetrics = request('GET', 'rest/v2/list_metrics/')
export const fieldValues = request('GET', 'rest/v2/field_values/')
export const seriesInfo = request('POST', 'rest/v2/series_info/')
export const saveView = request('POST', 'rest/v2/save_view/')
export const deleteLocation = request('POST', 'rest/v2/delete_location/')
export const addLocation = request('GET', 'rest/v2/add_location/')
export const getView = request('GET', 'rest/v2/view/')
export const viewGraph = request('POST', 'rest/v2/view_graph/')

export default {
  phoneReceiver,
  memberData,
  addMenu,
  editMenu,
  deleteMenu,
  listMetrics,
  fieldValues,
  seriesInfo,
  saveView,
  deleteLocation,
  addLocation,
  getView,
  viewGraph
}
