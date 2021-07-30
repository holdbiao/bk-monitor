import { request } from '../base'

export const alarmData = request('GET', 'rest/v1/event_center/alarm_data/')
export const alarmList = request('GET', 'rest/v1/event_center/alarm_list/')
export const alarmDetailChartData = request('GET', 'rest/v1/event_center/alarm_detail_chart_data/')
export const alarmNumData = request('GET', 'rest/v1/event_center/alarm_num_data/')
export const alarmDetailChartList = request('GET', 'rest/v1/event_center/alarm_detail_chart_list/')
export const alarmTypeInfo = request('GET', 'rest/v1/event_center/alarm_type_info/')

export default {
  alarmData,
  alarmList,
  alarmDetailChartData,
  alarmNumData,
  alarmDetailChartList,
  alarmTypeInfo
}
