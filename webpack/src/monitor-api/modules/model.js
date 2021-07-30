import { request } from '../base'

export const countReadOnlyModel = request('GET', 'rest/v1/read_only_model/count/')
export const listReadOnlyModel = request('GET', 'rest/v1/read_only_model/')
export const retrieveReadOnlyModel = request('GET', 'rest/v1/read_only_model/{pk}/')
export const countModel = request('GET', 'rest/v1/model/count/')
export const createModel = request('POST', 'rest/v1/model/')
export const destroyModel = request('DELETE', 'rest/v1/model/{pk}/')
export const listModel = request('GET', 'rest/v1/model/')
export const partialUpdateModel = request('PATCH', 'rest/v1/model/{pk}/')
export const retrieveModel = request('GET', 'rest/v1/model/{pk}/')
export const updateModel = request('PUT', 'rest/v1/model/{pk}/')
export const countBaseAlarm = request('GET', 'rest/v1/base_alarm/count/')
export const listBaseAlarm = request('GET', 'rest/v1/base_alarm/')
export const retrieveBaseAlarm = request('GET', 'rest/v1/base_alarm/{pk}/')
export const countSnapshotHostIndex = request('GET', 'rest/v1/snapshot_host_index/count/')
export const listSnapshotHostIndex = request('GET', 'rest/v1/snapshot_host_index/')
export const retrieveSnapshotHostIndex = request('GET', 'rest/v1/snapshot_host_index/{pk}/')
export const countRolePermission = request('GET', 'rest/v1/role_permission/count/')
export const createRolePermission = request('POST', 'rest/v1/role_permission/')
export const destroyRolePermission = request('DELETE', 'rest/v1/role_permission/{pk}/')
export const listRolePermission = request('GET', 'rest/v1/role_permission/')
export const partialUpdateRolePermission = request('PATCH', 'rest/v1/role_permission/{pk}/')
export const retrieveRolePermission = request('GET', 'rest/v1/role_permission/{pk}/')
export const updateRolePermission = request('PUT', 'rest/v1/role_permission/{pk}/')
export const countIndexColorConf = request('GET', 'rest/v1/index_color_conf/count/')
export const listIndexColorConf = request('GET', 'rest/v1/index_color_conf/')
export const retrieveIndexColorConf = request('GET', 'rest/v1/index_color_conf/{pk}/')
export const countUserConfig = request('GET', 'rest/v1/user_config/count/')
export const createUserConfig = request('POST', 'rest/v1/user_config/')
export const destroyUserConfig = request('DELETE', 'rest/v1/user_config/{pk}/')
export const listUserConfig = request('GET', 'rest/v1/user_config/')
export const partialUpdateUserConfig = request('PATCH', 'rest/v1/user_config/{pk}/')
export const retrieveUserConfig = request('GET', 'rest/v1/user_config/{pk}/')
export const updateUserConfig = request('PUT', 'rest/v1/user_config/{pk}/')
export const countApplicationConfig = request('GET', 'rest/v1/application_config/count/')
export const createApplicationConfig = request('POST', 'rest/v1/application_config/')
export const destroyApplicationConfig = request('DELETE', 'rest/v1/application_config/{pk}/')
export const listApplicationConfig = request('GET', 'rest/v1/application_config/')
export const partialUpdateApplicationConfig = request('PATCH', 'rest/v1/application_config/{pk}/')
export const retrieveApplicationConfig = request('GET', 'rest/v1/application_config/{pk}/')
export const updateApplicationConfig = request('PUT', 'rest/v1/application_config/{pk}/')
export const countGlobalConfig = request('GET', 'rest/v1/global_config/count/')
export const listGlobalConfig = request('GET', 'rest/v1/global_config/')
export const retrieveGlobalConfig = request('GET', 'rest/v1/global_config/{pk}/')
export const countOperateRecord = request('GET', 'rest/v1/operate_record/count/')
export const listOperateRecord = request('GET', 'rest/v1/operate_record/')
export const retrieveOperateRecord = request('GET', 'rest/v1/operate_record/{pk}/')
export const countMonitorLocation = request('GET', 'rest/v1/monitor_location/count/')
export const createMonitorLocation = request('POST', 'rest/v1/monitor_location/')
export const destroyMonitorLocation = request('DELETE', 'rest/v1/monitor_location/{pk}/')
export const listMonitorLocation = request('GET', 'rest/v1/monitor_location/')
export const partialUpdateMonitorLocation = request('PATCH', 'rest/v1/monitor_location/{pk}/')
export const retrieveMonitorLocation = request('GET', 'rest/v1/monitor_location/{pk}/')
export const updateMonitorLocation = request('PUT', 'rest/v1/monitor_location/{pk}/')
export const listAlarmType = request('GET', 'rest/v1/alarm_type/')
export const countUptimeCheckNode = request('GET', 'rest/v2/uptime_check/uptime_check_node/count/')
export const createUptimeCheckNode = request('POST', 'rest/v2/uptime_check/uptime_check_node/')
export const destroyUptimeCheckNode = request('DELETE', 'rest/v2/uptime_check/uptime_check_node/{pk}/')
export const fixNameConflictUptimeCheckNode = request('GET', 'rest/v2/uptime_check/uptime_check_node/fix_name_conflict/')
export const isExistUptimeCheckNode = request('GET', 'rest/v2/uptime_check/uptime_check_node/is_exist/')
export const listUptimeCheckNode = request('GET', 'rest/v2/uptime_check/uptime_check_node/')
export const partialUpdateUptimeCheckNode = request('PATCH', 'rest/v2/uptime_check/uptime_check_node/{pk}/')
export const retrieveUptimeCheckNode = request('GET', 'rest/v2/uptime_check/uptime_check_node/{pk}/')
export const updateUptimeCheckNode = request('PUT', 'rest/v2/uptime_check/uptime_check_node/{pk}/')
export const changeStatusUptimeCheckTask = request('POST', 'rest/v2/uptime_check/uptime_check_task/{pk}/change_status/')
export const cloneUptimeCheckTask = request('POST', 'rest/v2/uptime_check/uptime_check_task/{pk}/clone/')
export const countUptimeCheckTask = request('GET', 'rest/v2/uptime_check/uptime_check_task/count/')
export const createUptimeCheckTask = request('POST', 'rest/v2/uptime_check/uptime_check_task/')
export const deployUptimeCheckTask = request('POST', 'rest/v2/uptime_check/uptime_check_task/{pk}/deploy/')
export const destroyUptimeCheckTask = request('DELETE', 'rest/v2/uptime_check/uptime_check_task/{pk}/')
export const listUptimeCheckTask = request('GET', 'rest/v2/uptime_check/uptime_check_task/')
export const partialUpdateUptimeCheckTask = request('PATCH', 'rest/v2/uptime_check/uptime_check_task/{pk}/')
export const retrieveUptimeCheckTask = request('GET', 'rest/v2/uptime_check/uptime_check_task/{pk}/')
export const runningStatusUptimeCheckTask = request('GET', 'rest/v2/uptime_check/uptime_check_task/{pk}/running_status/')
export const testUptimeCheckTask = request('POST', 'rest/v2/uptime_check/uptime_check_task/test/')
export const updateUptimeCheckTask = request('PUT', 'rest/v2/uptime_check/uptime_check_task/{pk}/')
export const addTaskUptimeCheckGroup = request('POST', 'rest/v2/uptime_check/uptime_check_group/{pk}/add_task/')
export const createUptimeCheckGroup = request('POST', 'rest/v2/uptime_check/uptime_check_group/')
export const destroyUptimeCheckGroup = request('DELETE', 'rest/v2/uptime_check/uptime_check_group/{pk}/')
export const listUptimeCheckGroup = request('GET', 'rest/v2/uptime_check/uptime_check_group/')
export const partialUpdateUptimeCheckGroup = request('PATCH', 'rest/v2/uptime_check/uptime_check_group/{pk}/')
export const retrieveUptimeCheckGroup = request('GET', 'rest/v2/uptime_check/uptime_check_group/{pk}/')
export const updateUptimeCheckGroup = request('PUT', 'rest/v2/uptime_check/uptime_check_group/{pk}/')
export const checkIdCollectorPlugin = request('GET', 'rest/v2/collector_plugin/check_id/')
export const createCollectorPlugin = request('POST', 'rest/v2/collector_plugin/')
export const deleteCollectorPlugin = request('POST', 'rest/v2/collector_plugin/delete/')
export const destroyCollectorPlugin = request('DELETE', 'rest/v2/collector_plugin/{pk}/')
export const editCollectorPlugin = request('POST', 'rest/v2/collector_plugin/{pk}/edit/')
export const exportPluginCollectorPlugin = request('GET', 'rest/v2/collector_plugin/{pk}/export_plugin/')
export const fetchDebugLogCollectorPlugin = request('GET', 'rest/v2/collector_plugin/{pk}/fetch_debug_log/')
export const importPluginCollectorPlugin = request('POST', 'rest/v2/collector_plugin/import_plugin/')
export const listCollectorPlugin = request('GET', 'rest/v2/collector_plugin/')
export const operatorSystemCollectorPlugin = request('GET', 'rest/v2/collector_plugin/operator_system/')
export const partialUpdateCollectorPlugin = request('PATCH', 'rest/v2/collector_plugin/{pk}/')
export const releaseCollectorPlugin = request('POST', 'rest/v2/collector_plugin/{pk}/release/')
export const replacePluginCollectorPlugin = request('POST', 'rest/v2/collector_plugin/replace_plugin/')
export const retrieveCollectorPlugin = request('GET', 'rest/v2/collector_plugin/{pk}/')
export const startDebugCollectorPlugin = request('POST', 'rest/v2/collector_plugin/{pk}/start_debug/')
export const stopDebugCollectorPlugin = request('POST', 'rest/v2/collector_plugin/{pk}/stop_debug/')
export const tagOptionsCollectorPlugin = request('GET', 'rest/v2/collector_plugin/tag_options/')
export const updateCollectorPlugin = request('PUT', 'rest/v2/collector_plugin/{pk}/')
export const uploadFileCollectorPlugin = request('POST', 'rest/v2/collector_plugin/upload_file/')
export const createQueryHistory = request('POST', 'rest/v2/query_history/')
export const destroyQueryHistory = request('DELETE', 'rest/v2/query_history/{pk}/')
export const listQueryHistory = request('GET', 'rest/v2/query_history/')
export const partialUpdateQueryHistory = request('PATCH', 'rest/v2/query_history/{pk}/')
export const retrieveQueryHistory = request('GET', 'rest/v2/query_history/{pk}/')
export const updateQueryHistory = request('PUT', 'rest/v2/query_history/{pk}/')

export default {
  countReadOnlyModel,
  listReadOnlyModel,
  retrieveReadOnlyModel,
  countModel,
  createModel,
  destroyModel,
  listModel,
  partialUpdateModel,
  retrieveModel,
  updateModel,
  countBaseAlarm,
  listBaseAlarm,
  retrieveBaseAlarm,
  countSnapshotHostIndex,
  listSnapshotHostIndex,
  retrieveSnapshotHostIndex,
  countRolePermission,
  createRolePermission,
  destroyRolePermission,
  listRolePermission,
  partialUpdateRolePermission,
  retrieveRolePermission,
  updateRolePermission,
  countIndexColorConf,
  listIndexColorConf,
  retrieveIndexColorConf,
  countUserConfig,
  createUserConfig,
  destroyUserConfig,
  listUserConfig,
  partialUpdateUserConfig,
  retrieveUserConfig,
  updateUserConfig,
  countApplicationConfig,
  createApplicationConfig,
  destroyApplicationConfig,
  listApplicationConfig,
  partialUpdateApplicationConfig,
  retrieveApplicationConfig,
  updateApplicationConfig,
  countGlobalConfig,
  listGlobalConfig,
  retrieveGlobalConfig,
  countOperateRecord,
  listOperateRecord,
  retrieveOperateRecord,
  countMonitorLocation,
  createMonitorLocation,
  destroyMonitorLocation,
  listMonitorLocation,
  partialUpdateMonitorLocation,
  retrieveMonitorLocation,
  updateMonitorLocation,
  listAlarmType,
  countUptimeCheckNode,
  createUptimeCheckNode,
  destroyUptimeCheckNode,
  fixNameConflictUptimeCheckNode,
  isExistUptimeCheckNode,
  listUptimeCheckNode,
  partialUpdateUptimeCheckNode,
  retrieveUptimeCheckNode,
  updateUptimeCheckNode,
  changeStatusUptimeCheckTask,
  cloneUptimeCheckTask,
  countUptimeCheckTask,
  createUptimeCheckTask,
  deployUptimeCheckTask,
  destroyUptimeCheckTask,
  listUptimeCheckTask,
  partialUpdateUptimeCheckTask,
  retrieveUptimeCheckTask,
  runningStatusUptimeCheckTask,
  testUptimeCheckTask,
  updateUptimeCheckTask,
  addTaskUptimeCheckGroup,
  createUptimeCheckGroup,
  destroyUptimeCheckGroup,
  listUptimeCheckGroup,
  partialUpdateUptimeCheckGroup,
  retrieveUptimeCheckGroup,
  updateUptimeCheckGroup,
  checkIdCollectorPlugin,
  createCollectorPlugin,
  deleteCollectorPlugin,
  destroyCollectorPlugin,
  editCollectorPlugin,
  exportPluginCollectorPlugin,
  fetchDebugLogCollectorPlugin,
  importPluginCollectorPlugin,
  listCollectorPlugin,
  operatorSystemCollectorPlugin,
  partialUpdateCollectorPlugin,
  releaseCollectorPlugin,
  replacePluginCollectorPlugin,
  retrieveCollectorPlugin,
  startDebugCollectorPlugin,
  stopDebugCollectorPlugin,
  tagOptionsCollectorPlugin,
  updateCollectorPlugin,
  uploadFileCollectorPlugin,
  createQueryHistory,
  destroyQueryHistory,
  listQueryHistory,
  partialUpdateQueryHistory,
  retrieveQueryHistory,
  updateQueryHistory
}
