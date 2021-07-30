import { request } from '../base'

export const getGraphQueryConfig = request('POST', 'rest/v2/data_explorer/get_graph_query_config/')
export const savePanelOrder = request('POST', 'rest/v2/data_explorer/save_panel_order/')
export const deletePanelOrder = request('POST', 'rest/v2/data_explorer/delete_panel_order/')

export default {
  getGraphQueryConfig,
  savePanelOrder,
  deletePanelOrder
}
