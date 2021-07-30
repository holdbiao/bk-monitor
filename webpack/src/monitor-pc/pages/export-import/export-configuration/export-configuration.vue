<template>
  <div class="export" v-bkloading="{ isLoading: loading }">
    <!-- 搜索——下拉选框 组件 -->
    <select-input ref="selectInput"
                  :parent-loading="loading"
                  :default-value="defaultValue"
                  @change-table-loading="handleChangeLoading"
                  @select-data="handleChangeSelectData">
    </select-input>
    <div class="export-table">
      <!-- 表格 组件 -->
      <export-configuration-form
        v-for="(item, index) in exportData"
        :key="item.name"
        :class="{ 'view-border': index === exportData.length - 1 }"
        :list="item.list"
        :name="item.name"
        :route-name="item.routeName"
        :checked="item.checked"
        @check-change="handleCheckChange(...arguments, index)">
      </export-configuration-form>
    </div>
    <bk-button theme="primary" :disabled="isdisable" @click="handleSubmit" class="btn"> {{ $t('开始导出') }} </bk-button>
    <bk-button @click="handleCancel" class="cancel"> {{ $t('取消') }} </bk-button>
    <!-- 导出dialog框 组件 -->
    <export-configuration-dialog :state="state" :package-num="packageNum" :show.sync="dialogShow" :message="message"></export-configuration-dialog>
  </div>
</template>

<script>
import selectInput from './select-input'
import exportConfigurationForm from './export-configuration-forms'
import exportConfigurationDialog from './export-configuration-dialog'
import { exportPackage } from '../../../../monitor-api/modules/export_import'
import { queryAsyncTaskResult } from '../../../../monitor-api/modules/commons'
import { mapActions } from 'vuex'
import * as importExportAuth from '../authority-map'
import authorityMixinCreate from '../../../mixins/authorityMixin'
export default {
  name: 'export-configuration',
  components: {
    selectInput,
    exportConfigurationForm,
    exportConfigurationDialog
  },
  mixins: [authorityMixinCreate(importExportAuth)],
  provide() {
    return {
      authority: this.authority,
      handleShowAuthorityDetail: this.handleShowAuthorityDetail
    }
  },
  data() {
    return {
      loading: false,
      exportData: [], // 所有的导出目录
      dialogShow: false,
      timer: null,
      state: 'PREPARE_FILE',
      message: '',
      defaultValue: {
        value: 1
      },
      packageNum: {}, // dialog里面对应的导出条数
      listMap: [ // 勾选的ID会存到对应的checked里面
        {
          name: this.$t('采集配置'),
          id: 'collectConfigList',
          routeName: 'collect-config',
          checked: []
        },
        {
          name: this.$t('策略配置'),
          id: 'strategyConfigList',
          routeName: 'strategy-config-detail',
          checked: []
        },
        {
          name: this.$t('视图配置'),
          id: 'viewConfigList',
          routeName: '',
          checked: []
        }
      ]
    }
  },
  computed: {
    // 未勾选不能导出
    isdisable() {
      return this.listMap.every(item => item.checked.length === 0)
    }
  },
  // created () {
  //     this.getTableList()
  // },
  beforeRouteEnter(to, from, next) {
    next((vm) => {
      const routeParams = vm.$route.params
      vm.defaultValue.routeName = from.name || ''
      // 如果是服务分类跳转，则不调用getAllExportList
      if (from.name === 'service-classify') {
        vm.loading = true
        vm.defaultValue.value = 3
        vm.defaultValue.serverFirst = routeParams.first
        vm.defaultValue.serverSecond = routeParams.second
      } else {
        vm.getTableList()
      }
    })
  },
  beforeDestroy() {
    clearTimeout(this.timer)
  },
  methods: {
    ...mapActions('export', ['getAllExportList']),
    // 获取导出列表事件
    async getTableList(params = {}) {
      this.loading = true // 导出列表接口
      const data = await this.getAllExportList(params)
      this.handleChangeSelectData(data)
      this.loading = false
    },
    // 筛选事件
    handleChangeSelectData(data) {
      this.exportData = this.listMap.map(item => ({
        name: item.name,
        list: data[item.id],
        routeName: item.routeName
      }))
    },
    // 勾选变更事件
    handleCheckChange(value, index) {
      this.listMap[index].checked = value
    },
    // 开始导出和重试事件
    handleSubmit() {
      this.state = 'PREPARE_FILE'
      this.packageNum = {}
      let num = 0
      const polling = (params, callBack) => {
        queryAsyncTaskResult(params).then((data) => {
          if (!data.is_completed) {
            if (data.state === 'PENDING') {
              num += 1
              if (num > 25) {
                clearTimeout(this.timer)
                const result = {
                  is_completed: true,
                  state: 'FAILURE',
                  message: this.$t('请求超时')
                }
                callBack(result)
                return
              }
            }
            this.timer = setTimeout(() => {
              polling(params, callBack)
              clearTimeout(this.timer)
            }, 500)
          }
          callBack(data)
        })
          .catch((err) => {
            const result = {
              is_completed: true,
              state: 'FAILURE',
              data: err.data,
              message: err.message
            }
            callBack(result)
          })
      }
      const params = {
        collect_config_ids: this.listMap[0].checked,
        strategy_config_ids: this.listMap[1].checked,
        view_config_ids: this.listMap[2].checked
      }
      this.dialogShow = true
      // 导出配置接口
      exportPackage(params, { isAsync: true }).then((data) => {
        polling(data, (data) => {
          this.state = data.state
          if (data.state === 'MAKE_PACKAGE' && data.data) {
            this.packageNum = data.data
          }
          if (data.state === 'SUCCESS') {
            let url = data.data.download_path
            if (data.data.download_path.indexOf('http') !== 0) {
              url = process.env.NODE_ENV === 'development'
                ? `${process.env.proxyUrl}/media${data.data.download_path}`
                : `${window.location.origin}${window.site_url}media${data.data.download_path}`
            }
            // 创建a标签的方式不会弹新窗口
            const element = document.createElement('a')
            element.setAttribute('href', `${url}/${data.data.download_name}`)
            element.setAttribute('download', data.data.download_name)
            element.style.display = 'none'
            document.body.appendChild(element)
            element.click()
            document.body.removeChild(element)
            this.dialogShow = false
          }
          if (data.state === 'FAILURE') {
            this.state = data.state
            this.message = data.message
          }
        })
      })
        .catch((err) => {
          this.state = 'FAILURE'
          this.message = err.message
        })
    },
    // select-input 派发的loading事件
    handleChangeLoading(v) {
      this.loading = v
    },
    // 取消按钮事件
    handleCancel() {
      this.$router.push({ name: 'export-import' })
    }
  }
}
</script>

<style lang="scss" scoped>
    .export {
      font-size: 12px;
      color: #63656e;
      &-table {
        height: calc(100vh - 204px);
        display: flex;
        width: 100%;
        background: #fff;
        margin-bottom: 20px;
        .view-border {
          border-right: 1px solid #dcdee5;
        }
      }
      .btn {
        margin-right: 8px;
      }
      .cancel {
        width: 88px;
      }
    }
</style>
