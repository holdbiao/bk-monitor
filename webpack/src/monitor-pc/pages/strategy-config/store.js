
export default class TableStore {
  constructor(originData, bizList) {
    this.setDefaultStore()
    this.total = originData.length || 0
    this.data = []
    let i = 0
    while (i < this.total) {
      const item = originData[i]
      const targetString = ''
      const objectType = item.target_object_type
      const nodeType = item.target_node_type
      const biz = bizList.find(v => v.id === item.bk_biz_id) || { text: '' }
      this.data.push({
        id: item.id,
        bizId: item.bk_biz_id,
        bizName: biz.text,
        strategyName: item.name,
        strategyType: item.scenario,
        firstLabelName: item.first_label_name,
        secondLabelName: item.second_label_name,
        targetNodeType: nodeType,
        objectType,
        dataOrigin: item.data_source_type,
        targetNodesCount: item.target_nodes_count,
        totalInstanceCount: item.total_instance_count,
        target: targetString,
        noticeGroupList: item.notice_group_id_list,
        labels: item.labels,
        categoryList: Array.isArray(item.service_category_data) ? item.service_category_data : [],
        updator: item.update_user,
        updateTime: item.update_time.slice(0, item.update_time.indexOf('+')),
        addAllowed: item.add_allowed,
        enabled: item.is_enabled,
        legacy: item.is_legacy,
        canDelete: item.delete_allowed,
        canEdit: item.edit_allowed,
        overflow: false,
        overflowLabel: false,
        shieldInfo: item.shield_info,
        abnormalAlertCount: item.abnormal_alert_count,
        metricDescriptionList: item.metric_description_list,
        itemDescription: this.getItemDescription(item.item_list)
      })
      i += 1
    }
    // this.data = originData
  }

  getTableData() {
    // let ret = this.data
    // if (this.keyword.length) {
    //     const keyword = this.keyword.toLocaleLowerCase()
    //     ret = ret.filter(item => item.strategyName.toLocaleLowerCase().includes(keyword))
    // }
    // this.total = ret.length
    return this.data.slice(0, this.pageSize)
  }

  setDefaultStore() {
    this.keyword = ''
    this.page = 1
    this.pageSize = +localStorage.getItem('__common_page_size__') || 10
    this.pageList = [10, 20, 50, 100]
  }
  getItem(v) {
    if (v) {
      return v
    }
    return ''
  }
  getItemDescription(itemlist) {
    if (!itemlist) {
      return {
        tip: {
          content: '--',
          delay: 200
        },
        val: '--'
      }
    }
    // eslint-disable-next-line prefer-destructuring
    const item = itemlist[0]
    const metricField = this.getItem(item.metric_field)
    const metricFieldName = this.getItem(item.metric_field_name)
    const resultTableId = this.getItem(item.result_table_id)
    const itemName = this.getItem(item.item_name)
    const keywordsQueryString = this.getItem(item.keywords_query_string)
    const templates = {
      bk_monitor: {
        time_series: `${itemName}(${resultTableId}.${metricField})`,
        event: `${itemName}`,
        log: `${itemName}`
      },
      bk_data: {
        time_series: `${metricFieldName}(${resultTableId}.${metricField})`
      },
      bk_log_search: {
        time_series: `${metricField}(${window.i18n.t('索引集')}:${itemName})`,
        log: `${keywordsQueryString}(${window.i18n.t('索引集')}:${itemName})`
      },
      custom: {
        event: `${itemName}(${window.i18n.t('数据ID')}:${resultTableId})`,
        time_series: `${itemName}(${resultTableId}.${metricField})`
      }
    }
    const tipTemplates = {
      bk_log_search: {
        time_series: {
          html: `<div class="item-description">
            ${metricField}<span style="color:#c4c6cc;margin-left:12px">(
            ${window.i18n.t('索引集')}:${itemName})</span></div>`,
          allowHtml: true,
          content: '.item-description',
          delay: 200
        },
        log: {
          html: `<div class="item-description">${keywordsQueryString}
          <span style="color:#c4c6cc;margin-left:12px">(${window.i18n.t('索引集')}:${itemName})</span></div>`,
          allowHtml: true,
          content: '.item-description',
          delay: 200
        }
      }
    }
    const val = templates[item.data_source_label][item.data_type_label]
    const tipVal = tipTemplates[item.data_source_label]
      ? tipTemplates[item.data_source_label][item.data_type_label] : val
    return {
      tip: tipVal,
      val
    }
  }
}
