export default class TableStore {
  public data: {
    id: string
    bizId: string
    shieldType: string
    shieldTypeName: string
    shieldContent: string
    beginTime: string
    cycleDuration: string
    failureTime: string
    description: string
    status: string
    dimensionConfig: string
  }[]
  public keyword: string
  public count: number
  public page: number
  public pageSize: number
  public pageList: number[]
  public constructor(originData = [], count) {
    this.data = []
    this.setDefaultStore()
    this.setDefaultData(originData)
    this.count = count
  }

  public getTableData() {
    return this.data.slice(0, this.pageSize)
  }

  public setDefaultData(originData) {
    this.data = []
    let i = 0
    while (i < originData.length) {
      const item = originData[i]
      this.data.push({
        id: item.id,
        bizId: item.bk_biz_id,
        shieldType: item.category,
        shieldTypeName: item.category_name,
        shieldContent: item.content,
        beginTime: item.begin_time,
        cycleDuration: item.cycle_duration,
        failureTime: item.failure_time,
        description: item.description,
        status: item.status,
        dimensionConfig: item.dimension_config
      })
      i += 1
    }
  }

  public setDefaultStore() {
    this.keyword = ''
    this.page = 1
    this.pageSize = +localStorage.getItem('__common_page_size__') || 10
    this.pageList = [10, 20, 50, 100]
    this.count = 0
  }
}
