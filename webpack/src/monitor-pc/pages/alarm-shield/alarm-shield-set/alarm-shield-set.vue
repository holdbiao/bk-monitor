<template>
  <div class="alarm-shield-config" v-bkloading="{ 'isLoading': loading || inLoading }">
    <ul class="tab-list">
      <li class="tab-list-item"
          v-for="(item, index) in tab.list"
          :class="{ 'tab-active': index === tab.active }"
          :key="item.name"
          v-show="$route.name === 'alarm-shield-edit' ? item.componentName === curComponent : item.componentName !== 'alarm-shield-event'"
          @click="handleTabChange(index, item.componentName)"
      >
        <span class="tab-name">{{item.name}}</span>
      </li>
      <li class="tab-list-blank"></li>
    </ul>
    <div class="set-config-wrapper">
      <keep-alive>
        <component :is="curComponent" :shield-data="shieldData" :loading.sync="loading" :edit="edit"></component>
      </keep-alive>
    </div>

  </div>
</template>
<script>
import AlarmShieldScope from './alarm-shield-scope/alarm-shield-scope'
import AlarmShieldStrategy from './alarm-shield-strategy'
import AlarmShieldEvent from './alarm-shield-event'
import { frontendShieldDetail } from '../../../../monitor-api/modules/shield'
export default {
  name: 'alarm-shield-set',
  components: {
    AlarmShieldScope,
    AlarmShieldStrategy,
    AlarmShieldEvent
  },
  data() {
    return {
      inLoading: false,
      loading: false,
      tab: {
        active: 0,
        list: [
          { name: this.$t('基于范围进行屏蔽'), id: 0, componentName: 'alarm-shield-scope' },
          { name: this.$t('基于策略进行屏蔽'), id: 1, componentName: 'alarm-shield-strategy' },
          { name: this.$t('基于告警事件进行屏蔽'), id: 2, componentName: 'alarm-shield-event' }
        ]
      },
      curComponent: '',
      typeMap: {
        scope: 'alarm-shield-scope',
        strategy: 'alarm-shield-strategy',
        event: 'alarm-shield-event'
      },
      shieldData: {},
      edit: false
    }
  },
  beforeRouteEnter(to, from, next) {
    next((vm) => {
      if (to.name === 'alarm-shield-edit') {
        vm.handleGetShieldDetail()
        vm.curComponent = vm.typeMap[to.params.type]
        const index = vm.tab.list.findIndex(item => item.componentName === vm.curComponent)
        vm.tab.active = vm.tab.list[index].id
      } else {
        vm.curComponent = 'alarm-shield-scope'
      }
    })
  },
  async beforeRouteLeave(to, from, next) {
    if (!to.params.refresh) {
      const needNext = await this.handleCancel(false)
      next(needNext)
    } else {
      next()
    }
  },
  methods: {
    handleTabChange(index, componentName) {
      if (this.tab.active !== index) {
        this.tab.active = index
        this.curComponent = componentName
      }
    },
    handleCancel(needBack = true) {
      return new Promise((resolve) => {
        this.$bkInfo({
          title: this.$t('是否放弃本次操作？'),
          confirmFn: () => {
            needBack && this.$router.back()
            resolve(true)
          },
          cancelFn: () => resolve(false)
        })
      })
    },
    handleGetShieldDetail() {
      this.edit = true
      this.loading = true
      this.$store.commit('app/SET_NAV_TITLE', this.$t('加载中...'))
      frontendShieldDetail({ id: this.$route.params.id }).then((data) => {
        this.shieldData = data
        this.$store.commit('app/SET_NAV_TITLE', `${this.$t('编辑')}（#${data.id}）`)
      })
        .catch(() => {
          this.$store.commit('app/SET_NAV_TITLE', this.$t(' '))
          this.loading = false
        })
        .finally(() => {
          this.loading = false
        })
    }
  }
}
</script>
<style lang="scss" scoped>
.alarm-shield-config {
  border: 1px solid #dcdee5;
  background: #fff;
  min-height: calc(100vh - 80px);
  .tab-list {
    display: flex;
    flex-direction: row;
    justify-content: flex-start;
    align-items: center;
    line-height: 42px;
    background: #fafbfd;
    padding: 0;
    margin: 0;
    font-size: 14px;
    &-item {
      flex: 0 0 213px;
      border-right: 1px solid #dcdee5;
      border-bottom: 1px solid #dcdee5;
      text-align: center;
      color: #63656e;
      font-weight: bold;
      &.tab-active {
        color: #3a84ff;
        background: #fff;
        border-bottom-color: transparent;
        font-weight: bold;
      }
      &:hover {
        cursor: pointer;
        color: #3a84ff;
        font-weight: bold;
      }
    }
    &-blank {
      flex: 1 1 auto;
      height: 42px;
      border-bottom: 1px solid #dcdee5;
    }
  }
}
</style>
