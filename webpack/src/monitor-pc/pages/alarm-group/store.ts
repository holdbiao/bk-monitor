export default class TableStore {
  public data: {id: string; name: string}[]
  public keyword: string
  public total: number
  public page: number
  public pageSize: number
  public pageList: number[]
  public constructor(originData) {
    originData.forEach((set) => {
      const item = set
      const row = window.cc_biz_list.find(v => v.id === item.bk_biz_id)
      item.bizName = row ? row.text : '--'
    })
    this.setDefaultStore()
    this.total = originData.length
    this.data = originData
  }

  public getTableData() {
    let ret = this.data
    const keyword = this.keyword.toLocaleLowerCase()
    if (this.keyword.length) {
      ret = ret.filter(item => item.name.toLocaleLowerCase().includes(keyword) || item.id.toString().includes(keyword))
    }
    this.total = ret.length
    return ret.slice(this.pageSize * (this.page - 1), this.pageSize * this.page)
  }

  public setDefaultStore() {
    this.keyword = ''
    this.page = 1
    this.pageSize = +localStorage.getItem('__common_page_size__') || 10
    this.pageList = [10, 20, 50, 100]
    this.total = 0
  }
}
