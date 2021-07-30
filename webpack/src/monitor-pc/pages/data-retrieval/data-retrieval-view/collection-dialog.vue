<!--

 -->
<template>
  <bk-dialog :value="isShow"
             header-position="left"
             width="480"
             :title="$t('收藏')"
             @after-leave="handleCloseDialog">
    <div class="collection-dialog" v-bkloading="{ isLoading: loading }">
      <!-- 仪表盘分组 -->
      <div class="dashboard-group" v-for="group in dashBoardList" :key="group.id">
        <!-- 分组名称 -->
        <div class="dashboard-group-title" @click="handleClickGroup(group.id)">
          <i class="icon-monitor file-icon" :class="groupData.checkId === group.id ? 'icon-mc-file-open' : 'icon-mc-file-close'"></i>
          {{ group.title }}
        </div>
        <!-- 仪表盘名称 -->
        <transition
          @before-enter="beforeEnter" @enter="enter" @after-enter="afterEnter"
          @before-leave="beforeLeave" @leave="leave" @after-leave="afterLeave">
          <div v-if="groupData.checkId === group.id">
            <!-- 新增仪表盘 -->
            <div class="add-row-input dashboard-input" v-if="dashboard.isShow">
              <bk-input :ref="`dashboardInput${group.id}`"
                        :placeholder="'输入仪表盘名称'" v-model="dashboard.name">
              </bk-input>
              <div class="input-icon" @click="handleAddDashboard(group.id)"><i class="bk-icon icon-check-1"></i></div>
              <div class="input-icon" @click="handleCloseDashboard"><i class="icon-monitor icon-mc-close"></i></div>
            </div>
            <div class="dashboard-group-child add-new" @click="handleShowDashboardAdd(group.id)" v-else>
              <i class="icon-monitor icon-mc-add"></i>
              {{ $t('新建仪表盘') }}
            </div>
            <!-- 仪表盘名字 -->
            <div v-for="item in group.dashboards" :key="item.id"
                 class="dashboard-group-child"
                 :class="{ 'dashboard-active': checkedDashboard.id === item.id }"
                 @click="handleAddCollection(item)">
              <span class="group-child-name">{{ item.title }}</span>
              <i class="bk-icon icon-check-1" v-if="checkedDashboard.id === item.id"></i>
            </div>
          </div>
        </transition>
      </div>
      <!-- 新增仪表盘分组 -->
      <div class="add-row-input group-input" v-if="groupData.isShow">
        <bk-input :placeholder="'输入目录名称'" v-model="groupData.name" ref="groupInput"
                  :left-icon="'icon-monitor icon-mc-file-close'">
        </bk-input>
        <div class="input-icon" @click="handleAddDashboardGroup"><i class="bk-icon icon-check-1"></i></div>
        <div class="input-icon" @click="handleCloseDashboardGroup"><i class="icon-monitor icon-mc-close"></i></div>
      </div>
      <div class="dashboard-group-title add-new" @click="handleShowGroupAdd" v-else>
        <i class="icon-monitor icon-mc-add"></i>
        {{ $t('添加新目录') }}
      </div>
    </div>
    <template #footer>
      <bk-button
        :loading="loading"
        theme="primary" @click="handleCollectionToDashboard(true)"
        :disabled="!Object.keys(checkedDashboard).length">{{ $t('收藏并跳转') }}</bk-button>
      <bk-button
        :loading="loading"
        theme="primary" @click="handleCollectionToDashboard(false)"
        :disabled="!Object.keys(checkedDashboard).length">{{ $t('直接收藏') }}</bk-button>
      <bk-button @click="handleCloseDialog">{{ $t('取消') }}</bk-button>
    </template>
  </bk-dialog>
</template>
<script lang="ts">
import { Mixins, Component, Prop, Ref, Watch } from 'vue-property-decorator'
import collapseMixin from '../../../mixins/collapseMixin'
import { getDirectoryTree, createDashboardOrFolder, saveToDashboard } from '../../../../monitor-api/modules/grafana'
import { ICheckedDashboard } from '../index'
import MonitorVue from '../../../types/index'
import { DASHBOARD_ID_KEY } from '../../../constant/constant'

@Component({
  name: 'collection-dialog'
})
export default class CollectionDialog extends Mixins(collapseMixin)<MonitorVue> {
  @Ref() readonly groupInput!: HTMLFormElement
  // 勾选的图表数据
  @Prop({ default: () => ([]) })
  collectionList: any[]

  @Prop({ default: false })
  isShow: boolean

  loading = false
  groupData = {
    checkId: -1,
    name: '',
    isShow: false
  }
  dashboard = {
    name: '',
    isShow: false
  }
  checkedDashboard: ICheckedDashboard = {} // 选定的仪表盘数据
  dashBoardList = [] // 仪表盘列表

  @Watch('isShow')
  async onIsShowChanged() {
    this.checkedDashboard = {}
    await this.getDashboardTree()
    this.groupData.checkId = this.dashBoardList[0].id
  }

  //  获取仪表盘列表
  async getDashboardTree() {
    this.loading = true
    this.dashBoardList = await getDirectoryTree().catch(() => ([]))
    this.loading = false
  }

  //  选择仪表盘分组
  handleClickGroup(id: number) {
    this.groupData.checkId = this.groupData.checkId === id ? -1 : id
  }

  //  选中要收藏的仪表盘
  handleAddCollection(dashboard) {
    if (this.checkedDashboard.id && this.checkedDashboard.id === dashboard.id) {
      this.checkedDashboard = {}
      return
    }
    this.checkedDashboard = dashboard
  }

  //  显示新增仪表盘分组input行
  handleShowGroupAdd() {
    this.groupData.isShow = true
    this.$nextTick(() => {
      this.groupInput.focus()
    })
  }

  //  关闭新增仪表盘分组input行
  handleCloseDashboardGroup() {
    this.groupData.name = ''
    this.groupData.isShow = false
  }

  //  新增仪表盘分组
  async handleAddDashboardGroup() {
    const { name } = this.groupData
    if (!name) return
    const params = {
      title: name,
      type: 'folder'
    }
    await createDashboardOrFolder(params).catch(() => {})
    await this.getDashboardTree()
    this.handleCloseDashboardGroup()
  }

  //  新增仪表盘
  async handleAddDashboard(id: number) {
    const { name } = this.dashboard
    if (!name) return
    const params = {
      title: name,
      type: 'dashboard',
      folderId: id
    }
    await createDashboardOrFolder(params).catch(() => {})
    await this.getDashboardTree()
    this.handleCloseDashboard()
  }

  //  显示新增仪表盘input行
  handleShowDashboardAdd(id: number) {
    this.dashboard.isShow = true
    this.$nextTick(() => {
      const dashboardRef: HTMLFormElement = this.$refs[`dashboardInput${id}`][0]
      dashboardRef.focus()
    })
  }

  //  收藏到仪表盘
  handleCollectionToDashboard(needJump = false) {
    this.loading = true
    const panels = this.collectionList.map(item => ({
      name: item.title,
      fill: item.fill,
      min_y_zero: item.min_y_zero,
      queries: item.targets.map(set => ({
        ...set.data,
        alias: set.alias
      }))
    }))
    saveToDashboard({
      panels,
      dashboard_uids: [this.checkedDashboard.uid]
    }).then(() => {
      this.$bkMessage({ theme: 'success', message: this.$t('收藏成功') })
      this.$emit('on-collection-success')
      this.$emit('update:isShow', false)
      // 跳转grafana
      if (needJump) {
        this.updateDashboardId(this.checkedDashboard.uid)
        const { href } = this.$router.resolve({
          name: 'grafana'
        })
        window.open(href, '_blank')
      }
    })
      .finally(() => {
        this.loading = false
      })
  }
  // 更新仪表盘默认显示
  updateDashboardId(uid: string) {
    let idObj = null
    const { bizId } = this.$store.getters
    const dashboardCache = localStorage.getItem(DASHBOARD_ID_KEY)
    if (dashboardCache && dashboardCache.indexOf('{') > -1) {
      const data = JSON.parse(dashboardCache)
      data[bizId] = uid
      idObj = JSON.stringify(data)
    } else {
      idObj = JSON.stringify({ [bizId]: uid })
    }
    localStorage.setItem(DASHBOARD_ID_KEY, idObj)
  }

  //  关闭新增仪表盘input行
  handleCloseDashboard() {
    this.dashboard.name = ''
    this.dashboard.isShow = false
  }

  //  关闭收藏dialog
  handleCloseDialog() {
    this.handleCloseDashboardGroup()
    this.handleCloseDashboard()
    this.$emit('update:isShow', false)
  }
}
</script>
<style lang="scss" scoped>
/deep/ .bk-dialog-wrapper .bk-dialog-header {
  padding: 3px 24px 14px;
}
.collection-dialog {
  border-top: 1px solid #f0f1f5;
  padding-bottom: 28px;
  .dashboard-group {
    display: flex;
    flex-direction: column;
    color: #313238;
    min-height: 42px;
    border-bottom: 1px solid #f0f1f5;
    &-title {
      display: flex;
      align-items: center;
      height: 42px;
      cursor: pointer;
      .file-icon {
        color: #a3c5fd;
        font-size: 18px;
        margin: 0 12px 0 2px;
      }
    }
    &-child {
      margin: 0 0 2px 32px;
      padding: 0 10px;
      height: 32px;
      display: flex;
      align-items: center;
      color: #63656e;
      background: #f5f6fa;
      border-radius: 2px;
      .group-child-name {
        flex: 1;
      }
      .icon-check-1 {
        color: #3a84ff;
        font-size: 24px;
      }
      &:nth-last-child(1) {
        margin-bottom: 11px;
      }
      &:hover {
        background: #e1ecff;
        cursor: pointer;
      }
    }
    .dashboard-active {
      background: #e1ecff;
    }
  }
  .add-new {
    color: #3a84ff;
    border-bottom: 1px solid #f0f1f5;
    display: flex;
    align-items: center;
    padding-left: 4px;
    .icon-mc-add {
      font-size: 24px;
    }
  }
  .add-row-input {
    display: flex;
    align-items: center;
    .input-icon {
      min-width: 32px;
      height: 32px;
      display: flex;
      align-items: center;
      justify-content: center;
      border: 1px solid #c4c6cc;
      border-radius: 2px;
      margin-left: 2px;
      font-size: 24px;
      background: #fff;
      &:hover {
        color: #3a84ff;
        border-color: #3a84ff;
        background: rgba(58, 132, 255, .06);
        cursor: pointer;
      }
    }
  }
  .group-input {
    height: 42px;
    border-bottom: 1px solid #f0f1f5;
    /deep/ .bk-form-control .control-icon {
      color: #979ba5;
    }
  }
  .dashboard-input {
    margin-left: 32px;
    background: #f5f6fa;
    margin-bottom: 2px;
  }
}
</style>
