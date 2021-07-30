
export default class TableStore {
  constructor(originData, bizName) {
    this.keyword = ''
    this.page = 1
    this.pageSize = +localStorage.getItem('__common_page_size__') || 10
    this.pageList = [5, 10, 20, 50, 100]
    this.total = originData.length
    this.data = []
    let i = 0
    while (i < this.total) {
      const item = originData[i]
      this.data.push({
        id: window.cc_biz_id,
        bizName,
        first: item.first,
        second: item.second,
        metricCount: item.metric_count,
        configCount: item.config_count,
        strategyCount: item.strategy_count
      })
      i += 1
    }
  }

  getTableData() {
    let ret = this.data
    if (this.keyword.length) {
      const keyword = this.keyword.toLocaleLowerCase()
      ret = ret.filter(item => item.first.toLocaleLowerCase().includes(keyword)
        || item.second.toLocaleLowerCase().includes(keyword))
    }
    this.total = ret.length
    return ret.slice(this.pageSize * (this.page - 1), this.pageSize * this.page)
  }
}
