/* eslint-disable prefer-destructuring */
import { Component, Vue } from 'vue-property-decorator'

@Component
export default class documentLinkMixin extends Vue {
  public getDateConfig(date) {
    const cycle = {
      begin_time: '',
      end_time: '',
      cycle_config: {
        begin_time: '',
        end_time: '',
        type: date.type,
        day_list: [],
        week_list: []
      }
    }
    if (date.type !== 1) {
      cycle.begin_time = date.dateRange[0]
      cycle.end_time = date.dateRange[1]
    }
    switch (date.type) {
      case 1:
        cycle.cycle_config.day_list = date.day.list
        cycle.begin_time = date.single.range[0]
        cycle.end_time = date.single.range[1]
        break
      case 2:
        cycle.cycle_config.day_list = date.day.list
        cycle.cycle_config.begin_time = date.day.range[0]
        cycle.cycle_config.end_time = date.day.range[1]
        break
      case 3:
        cycle.cycle_config.week_list = date.week.list
        cycle.cycle_config.begin_time = date.week.range[0]
        cycle.cycle_config.end_time = date.week.range[1]
        break
      case 4:
        cycle.cycle_config.day_list = date.month.list
        cycle.cycle_config.begin_time = date.month.range[0]
        cycle.cycle_config.end_time = date.month.range[1]
        break
    }
    return cycle
  }
}
