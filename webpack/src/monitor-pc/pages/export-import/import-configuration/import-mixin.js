import { debounce } from 'throttle-debounce'
import { addListener, removeListener } from 'resize-detector'
export default {
  data() {
    return {
      // collapse 数据
      collapse: {
        list: [
          {
            name: 'collect',
            title: this.$t('采集配置')
          },
          {
            name: 'strategy',
            title: this.$t('策略配置')
          },
          {
            name: 'view',
            title: this.$t('视图配置')
          },
          {
            name: 'plugin',
            title: this.$t('被关联插件'),
            markName: this.$t('被关联')
          }
        ],
        activeName: []
      },
      // 表格相关属性
      table: {
        list: [],
        statistics: {},
        firstCheckedAll: [],
        runingQueue: [],
        timer: null,
        interval: 300,
        selection: [],
        filterStatusName: this.$t('任务状态'),
        taskId: 0
      },
      listenResize() {},
      // 当前可视区域是否出现滚动（用于按钮悬浮）
      isScroll: false,
      loading: false
    }
  },
  computed: {
    // 统计当前表格状态数据
    statusHtml() {
      return (collapseName, filterStatus) => {
        const statusHtml = []
        Object.keys(this.statusMap).forEach((status) => {
          const statusCount = this.table.statistics[collapseName]
          if (statusCount?.[status] && (!filterStatus || filterStatus === 'total' || filterStatus === status)) {
            statusHtml.push(`
                        <span class="total-${status}">${statusCount[status]}</span>
                        <span>${this.$t('个')}${this.statusMap[status].name}</span>
                        `)
          }
        })
        return statusHtml.join('<span class="separator">,</span>')
      }
    }
  },
  mounted() {
    this.listenResize = debounce(200, v => this.handleResize(v))
    addListener(this.$el, this.listenResize)
  },
  beforeDestroy() {
    removeListener(this.$el, this.listenResize)
  },
  methods: {
    /**
     * 默认展开第一个有数据的 Collapse item
     */
    handleExpandCollapse() {
      this.collapse.activeName = []
      const data = this.collapse.list.find((item) => {
        const { name } = item
        return this.table.statistics[name] && this.table.statistics[name].total
      })
      if (data) {
        this.collapse.activeName.push(data.name)
      }
    },
    /**
     * 规整统计数据
     * @param {Object} data 统计数据
     */
    handleCountData(data) {
      if (!data) return {}
      return {
        collect: data.collectCount || {},
        plugin: data.pluginCount || {},
        strategy: data.strategyCount || {},
        view: data.viewCount || {},
        allCount: data.allCount || {}
      }
    },
    /**
     * 处理底部按钮组是否悬浮
     */
    handleResize() {
      if (!this.$el.parentElement) return
      this.isScroll = this.$el.scrollHeight > this.$el.parentElement.clientHeight
    }
  }
}
