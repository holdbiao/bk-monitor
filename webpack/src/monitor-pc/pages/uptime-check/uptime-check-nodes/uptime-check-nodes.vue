<template>
  <div class="node-page-container" v-monitor-loading="{ 'isLoading': loading }">
    <div v-show="!showCreateCard">
      <div class="header">
        <div class="create-node">
          <bk-button
            theme="primary"
            class="mc-btn-add"
            v-authority="{
              active: !authority.MANAGE_AUTH
            }"
            @click="authority.MANAGE_AUTH ? addNode() : handleShowAuthorityDetail(uptimeAuth.MANAGE_AUTH)">
            {{ $t('新建') }}
          </bk-button>
        </div>
        <bk-input :placeholder="$t('节点名称/IP')" right-icon="bk-icon icon-search" @change="search" :value="searchWord" style="width: 320px;" clearable></bk-input>
      </div>
      <div class="node-table">
        <bk-table
          :data="table.list"
          :empty-text="$t('查询无数据')"
          row-class-name="row-class">
          <bk-table-column width="153" :label="$t('节点名称')" prop="name"></bk-table-column>
          <bk-table-column label="IP / Url" prop="ip"></bk-table-column>
          <bk-table-column width="153" :label="$t('类型')" prop="is_common">
            <template slot-scope="scope">
              {{scope.row.is_common ? $t('自建节点(公共)') : $t('自建节点(私有)')}}
            </template>
          </bk-table-column>
          <bk-table-column v-if="false" :label="$t('所属业务')" prop="bk_biz_name"></bk-table-column>
          <bk-table-column :label="$t('国家/地区')" prop="country">
            <template slot-scope="scope">
              <div>{{scope.row.country ? scope.row.country : '--'}}</div>
            </template>
          </bk-table-column>
          <bk-table-column :label="$t('省份')" align="center">
            <template slot-scope="scope">
              <div>{{scope.row.province ? scope.row.province : '--'}}</div>
            </template>
          </bk-table-column>
          <bk-table-column :label="$t('关联任务数')" align="right">
            <template slot-scope="scope">
              <div class="task-num" :style="{ color: scope.row.task_num > 0 ? '#3A84FF' : '#C4C6CC' }" @click="scope.row.task_num > 0 && handleToCheckTask(scope.row.name)">{{scope.row.task_num || 0}}</div>
            </template>
          </bk-table-column>
          <bk-table-column :label="$t('外网运营商')" align="center">
            <template slot-scope="scope">
              <div>{{scope.row.carrieroperator ? scope.row.carrieroperator : '--'}}</div>
            </template>
          </bk-table-column>
          <bk-table-column :label="$t('状态')">
            <template slot-scope="scope">
              <span :class="['col-status', statusColorMap[scope.row.status].className]"
                    @mouseenter.stop="handleStatusPopoverShow(scope.row, scope.$index, $event)">
                {{statusColorMap[scope.row.status].text}}
              </span>
            </template>
          </bk-table-column>
          <bk-table-column :label="$t('操作')">
            <template slot-scope="scope">
              <div>
                <bk-button
                  v-authority="{ active: !authority.MANAGE_AUTH }"
                  theme="primary"
                  text
                  :class="[canEdit(scope.row) ? '' : 'not-allowed']"
                  :disabled="!canEdit(scope.row)"
                  @click="authority.MANAGE_AUTH ? handleEdit(scope.row) : handleShowAuthorityDetail(uptimeAuth.MANAGE_AUTH)">
                  {{ $t('编辑') }}
                </bk-button>
                <bk-button
                  v-authority="{ active: !authority.MANAGE_AUTH }"
                  text
                  :class="[canEdit(scope.row) ? '' : 'not-allowed']"
                  :disabled="!canEdit(scope.row)"
                  @click="authority.MANAGE_AUTH ? handleRemove(scope.row.id) : handleShowAuthorityDetail(uptimeAuth.MANAGE_AUTH)">
                  {{ $t('删除') }}
                </bk-button>
              </div>
            </template>
          </bk-table-column>
        </bk-table>
        <div class="uptime-check-node-footer" v-show="table.total">
          <bk-pagination
            class="list-pagination"
            @change="handlePageChange"
            @limit-change="handleLimitChange"
            align="right"
            :current.sync="table.page"
            :limit="table.pageSize"
            :count="table.total"
            :limit-list="table.pageList"
            show-total-count>
          </bk-pagination>
        </div>
      </div>
    </div>
    <div class="not-nodes" v-show="showCreateCard">
      <div class="desc"> {{ $t('暂无拨测节点') }} </div>
      <div class="create-node-el">
        <div class="title"> {{ $t('新建') }} </div>
        <div class="create-desc"> {{ $t('创建一个私有或云拨测节点，用于探测服务的质量与可用性') }} </div>
        <span class="create-btn"
              v-authority="{
                active: !authority.MANAGE_AUTH
              }"
              @click="authority.MANAGE_AUTH ? addNode() : handleShowAuthorityDetail(uptimeAuth.MANAGE_AUTH)">
          {{ $t('立即新建') }}
        </span>
      </div>
    </div>
    <div v-show="false">
      <div class="popover-content" ref="popoverContent">
        <div class="popover-hint">
          <div class="hint-upgrade" v-if="popover.data.status === '2'">
            <div class="hint-text"> {{ $t('当前采集器版本过低') }}（ {{popover.data.version}} ），{{ $t('请联系系统管理员升级至最新版本') }}（ {{popover.data.right_version}}）</div>
          </div>
          <div class="hint-deploy" v-else-if="popover.data.status === '-1'">
            <div class="hint-text">
              <span class="text-content"> {{ $t('bkmonitorbeat采集器异常或版本过低，请至节点管理处理') }} </span>
            </div>
            <div class="hint-btn">
              <bk-button class="btn-cancel" @click.stop="handleStatusPopoverHide" :text="true"> {{ $t('取消') }} </bk-button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script>
import { debounce } from 'throttle-debounce'
import { listUptimeCheckNode, destroyUptimeCheckNode } from '../../../../monitor-api/modules/model'
import { commonPageSizeMixin } from '../../../common/mixins'
export default {
  name: 'uptime-check-nodes',
  mixins: [commonPageSizeMixin],
  inject: ['authority', 'handleShowAuthorityDetail', 'uptimeAuth'],
  props: {
    fromRouteName: {
      type: String,
      required: true
    }
  },
  data() {
    return {
      loading: false,
      timer: null,
      intv: 1000, // 轮询间隔
      times: 0, // 轮询次数
      timesLimit: 20, // 轮询次数限制
      businessId: Number(this.$store.getters.bizId),
      searchWord: '',
      nodes: [],
      table: {
        list: [],
        loading: false,
        page: 1,
        pageSize: 10,
        pageList: [10, 20, 50, 100],
        total: 0
      },
      showCreateCard: false,
      statusColorMap: {
        0: {
          className: 'normal',
          text: this.$t('正常')
        },
        1: {
          className: 'initing',
          text: this.$t('初始化中')
        },
        '-1': {
          className: 'error',
          text: this.$t('异常')
        },
        2: {
          className: 'warning',
          text: this.$t('升级')
        }
      },
      search() {},
      popover: {
        active: -1,
        instance: null,
        data: {}
      }
    }
  },
  activated() {
    this.handleRouteEnter()
  },
  deactivated() {
    this.handleStatusPopoverHide()
  },
  created() {
    this.search = debounce(300, v => this.searchNode(v))
  },
  beforeDestroy() {
    this.timer && clearTimeout(this.timer)
    this.handleStatusPopoverHide()
  },
  methods: {
    handleRouteEnter(name) {
      if (!['uptime-check-node-add', 'uptime-check-node-edit'].includes(name)) {
        this.table.page = 1
        this.table.pageSize = this.handleGetCommonPageSize()
        this.table.total = 0
        this.searchWord = ''
      }
      !this.loading && this.getNodes()
    },
    handlePageChange(v) {
      this.table.page = v
      this.handleTableData()
    },
    handleTableData() {
      const tableData = this.nodes.filter(item => item.ip.indexOf(this.searchWord) > -1
      || item.name.indexOf(this.searchWord) > -1)
      const start = this.table.pageSize * (this.table.page - 1)
      const end = this.table.pageSize * this.table.page
      const data = tableData.slice(start, end)
      this.table.list = data
      this.table.total = tableData.length
    },
    handleLimitChange(size) {
      this.table.pageSize = size
      this.table.page = 1
      this.handleSetCommonPageSize(size)
      this.handleTableData()
    },
    handleRemove(id) {
      this.$bkInfo({
        title: this.$t('确认删除此节点?'),
        maskClose: true,
        confirmFn: () => {
          this.loading = true
          destroyUptimeCheckNode(id).then(() => {
            this.getNodes()
            this.$bkMessage({ theme: 'success', message: this.$t('删除成功') })
          })
            .catch(() => {})
            .finally(() => {
              this.loading = false
            })
        }
      })
    },
    getNodes(loading = true) {
      this.loading = loading
      return listUptimeCheckNode().then((data) => {
        this.showCreateCard = !data.length
        if (!this.showCreateCard) {
          this.nodes = data
          this.handleTableData()
        }
      })
        .finally(() => {
          this.loading = false
        })
    },
    searchNode(v) {
      this.searchWord = v
      this.table.page = 1
      this.handleTableData()
    },
    addNode() {
      this.$router.push({
        name: 'uptime-check-node-add'
      })
    },
    handleEdit(data) {
      this.$router.push({
        name: 'uptime-check-node-edit',
        params: {
          id: data.id,
          bizId: data.bk_biz_id,
          title: this.$t('编辑拨测节点')
        }
      })
    },
    pollNodeData() {
      if (this.times < this.timesLimit) {
        this.getNodes(false)
        this.timer = setTimeout(this.pollNodeData, this.intv)
        this.times += 1
      } else if (this.timer) {
        clearTimeout(this.timer)
        this.timer = null
        this.times = 0
      }
    },
    canEdit(row) {
      return row.bk_biz_id === this.businessId
    },
    handleStatusPopoverShow(row, index, e) {
      this.handleStatusPopoverHide()
      if (row.status !== '-1' && row.status !== '2') {
        return
      }
      const { popover } = this
      popover.data = row
      popover.instance = this.$bkPopover(e.target, {
        content: this.$refs.popoverContent,
        arrow: true,
        interactive: true,
        // interactiveBorder: 20,
        placement: 'bottom-start',
        theme: 'light task-node',
        maxWidth: 188,
        distance: 0,
        duration: [325, 300],
        // offset: '-35, 0',
        appendTo: () => e.target
      })
      // .instances[0]
      popover.instance.show(100)
    },
    handleStatusPopoverHide() {
      const { popover } = this
      if (popover.instance) {
        popover.instance.hide()
        popover.instance.destroy(true)
        popover.instance = null
      }
    },
    handleToCheckTask(name) {
      this.$emit('set-task', name)
      // this.SET_KEY_WORD(`${this.$t('节点：')}${name}`)
      // this.$store.commit('uptime-check-task/SET_KEY_WORD', )
    }
  }
}
</script>
<style lang="scss" scoped>
    .node-page-container {
      .header {
        display: flex;
        flex-wrap: wrap;
        justify-content: space-between;
        margin-bottom: 16px;
        .create-node {
          flex: 0 0 130px;
          padding-right: 10px;
          /deep/ .bk-button {
            padding: 0 17px;
          }
        }
        /deep/ .icon-search {
          cursor: pointer;
        }
      }
      .node-table {
        min-height: 513px;
        height: calc(100vh - 168px);
        /deep/ .bk-table {
          overflow: visible;
          .bk-table-body-wrapper {
            overflow: visible;
          }
        }
        /deep/ .row-class {
          color: #63656e;
        }
        .uptime-check-node-footer {
          background: #fff;
          border: 1px solid #dcdee5;
          padding: 15px;
          border-radius: 2px;
          border-top: 0;
          /deep/ .bk-page-count {
            margin-top: 0;
          }
        }
        .normal {
          color: #2dcb56;
        }
        .error {
          color: #ea3636;
          cursor: pointer;
        }
        .warning {
          color: #ffeb00;
          cursor: pointer;
        }
        .task-num {
          color: #3a84ff;
          cursor: pointer;
        }
        .not-allowed {
          cursor: not-allowed;
          color: #c4c6cc;
        }
        /deep/ .bk-button-text {
          padding-left: 0;
        }
        .col-status {
          display: inline-block;
          height: 42px;
          line-height: 42px;
          // width: 50%;
        }
      }
      .not-nodes {
        text-align: center;
        margin-top: 75px;
        .desc {
          font-size: 20px;
          margin-bottom: 32px;
          color: #313238;
        }
        .create-node-el {
          display: inline-block;
          width: 320px;
          height: 220px;
          background: #fff;
          border: 1px solid #f0f1f5;
          .title {
            margin: 40px auto 8px auto;
            font-size: 16px;
            color: #63656e;
            font-weight: bold;
          }
          .create-desc {
            margin: auto;
            width: 208px;
            line-height: 20px;
            font-size: 12px;
            color: #63656e;
          }
          .create-btn {
            margin-top: 24px;
            display: inline-block;
            height: 36px;
            line-height: 36px;
            width: 160px;
            border: 1px solid #699df4;
            border-radius: 18px;
            color: #699df4;
            cursor: pointer;
            font-size: 12px;
          }
        }
      }
    }
    .popover-content {
      line-height: normal;
      width: 188px;
      height: 78px;
      padding-top: 16px;
      padding-right: 16px;
      padding-left: 16px;
      .hint-title {
        margin-bottom: 15px;
        color: #606266;
        font-size: 12px;
      }
      .hint-text {
        height: 32px;
        .text-content {
          font-size: 12px;
          margin-bottom: 15px;
        }
      }
      .hint-btn {
        text-align: right;
        .btn-confirm {
          margin-right: 10px;
        }
        .btn-cancel {
          padding-right: 0;
        }
      }
    }
    /deep/ .tippy {
      &-popper {
        max-width: 188px;
      }
      &-tooltip {
        &.task-node-theme {
          padding: 0
        }
      }
    }
</style>
