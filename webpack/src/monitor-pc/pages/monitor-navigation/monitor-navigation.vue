<template>
  <div class="monitor-navigation" v-bkloading="{ isLoading: loading }" :class="$route.meta.navClass">
    <bk-navigation
      :class="{
        'no-need-menu': !header.needMenu,
        'custom-content': customContent
      }"
      @toggle="handleToggle"
      :need-menu="header.needMenu"
      :side-title="nav.title"
      @toggle-click="handleToggleClick"
      :default-open="nav.toggle">
      <div slot="header" class="monitor-navigation-header">
        <div class="header-title">
          <span v-if="$route.meta.needBack" @click="handleBack" class="header-title-back icon-monitor icon-back-left"></span>
          {{ navTitle && $t('route-' + navTitle).replace('route-', '') }}
          <i v-if="showCopyBtn"
             v-bk-tooltips="{ content: $t('复制链接') }"
             class="icon-monitor icon-copy-link monitor-copy-link"
             @click="handleCopyLink">
          </i>
          <template v-if="$route.name === 'grafana'">
            <set-menu
              ref="setMenu"
              @click="!hasDashboardAuth && handleUnDashboardAuth()"
              :has-auth="hasDashboardAuth"
              :menu-list="grafanaMenuList"
              @item-click="handleGrafanaMenuClick">
            </set-menu>
          </template>
        </div>
        <bk-select ref="headerSelect" class="header-select" search-with-pinyin v-model="header.select.value" @change="handleBizChange" searchable :clearable="false">
          <bk-option
            v-for="(option, index) in header.select.list"
            :key="index"
            :id="option.id"
            :name="option.text">
          </bk-option>
          <div slot="extension" class="select-extension">
            <span class="select-extension-btn has-border" @click="handleGetBizAuth">{{$t('申请业务权限')}}</span>
            <span class="select-extension-btn" @click="handleGotoDemo" v-if="hasDemoBiz">{{$t('体验DEMO')}}</span>
          </div>
        </bk-select>
        <bk-popover theme="light navigation-message" :arrow="false" offset="-20, 6" placement="bottom-start" :tippy-options="{ 'hideOnClick': false }">
          <div class="header-help is-left">
            <span class="help-icon icon-monitor icon-mc-help-fill"></span>
          </div>
          <template slot="content">
            <ul class="monitor-navigation-help">
              <li class="nav-item" v-for="(item, index) in help.list" :key="index" @click="handleHelp(item)">
                {{ item.name }}
              </li>
            </ul>
          </template>
        </bk-popover>
        <bk-popover theme="light navigation-message" :arrow="false" offset="-20, 10" placement="bottom-start" :tippy-options="{ 'hideOnClick': false }">
          <div class="header-user is-left">
            {{userName}}
            <i class="bk-icon icon-down-shape"></i>
          </div>
        </bk-popover>
      </div>
      <div class="monitor-logo" slot="side-icon">
        <img class="monitor-logo-icon" src="../../static/images/svg/monitor-logo.svg" />
      </div>
      <div slot="menu" class="monitor-menu">
        <bk-navigation-menu ref="menu" :default-active="defaultRouteId" :toggle-active="nav.toggle" :before-nav-change="handleBeforeNavChange">
          <template v-for="item in nav.list">
            <bk-navigation-menu-group
              v-if="item.children && !!item.children.length"
              :group-name="nav.toggle ? $t((item.navName || item.name)) : $t(item.shortName)"
              :key="item.name">
              <template v-for="child in item.children">
                <bk-navigation-menu-item
                  :key="child.id"
                  v-bind="child"
                  v-if="!child.hidden"
                  :href="getNavHref(child)"
                  @click="handleNavItemClick(child)"
                  :default-active="child.active">
                  <span>{{$t('route-' + (child.navName || child.name))}}</span>
                </bk-navigation-menu-item>
              </template>
            </bk-navigation-menu-group>
            <bk-navigation-menu-item
              :key="item.id"
              v-bind="item"
              v-else
              :href="getNavHref(item)"
              @click="handleNavItemClick(item)"
              :default-active="item.active">
              <span>{{$t('route-' + (item.navName || item.name))}}</span>
            </bk-navigation-menu-item>
          </template>
        </bk-navigation-menu>
      </div>
      <!-- eslint-disable-next-line vue/no-v-html-->
      <div slot="footer" style="width: 100%" v-if="$route.name === 'home'" v-html="footer.html">
      </div>
      <div v-bkloading="{ isLoading: mcMainLoading }" class="monitor-main-loading" v-show="mcMainLoading">
      </div>
      <template>
        <keep-alive>
          <router-view :toggle-set="nav.toggleSet" v-bind="Object.assign({}, $route.params, { title: '' })"></router-view>
        </keep-alive>
        <router-view key="noCache" v-bind="Object.assign({}, $route.params, { title: '' })" name="noCache" :toggle-set="nav.toggleSet"></router-view>
        <authority-modal></authority-modal>
      </template>
    </bk-navigation>
    <log-version :dialog-show.sync="log.show"></log-version>
    <bk-paas-login ref="login"></bk-paas-login>
  </div>
</template>

<script>
import LogVersion from '../../components/log-version/log-version'
import LogVersionMixin from '../../components/log-version/log-version-mixin'
import documentLinkMixin from '../../mixins/documentLinkMixin.ts'
import { createNamespacedHelpers } from 'vuex'
import { SET_BIZ_ID } from '../../store/modules/app'
import { copyText, getUrlParam, deleteCookie } from '../../../monitor-common/utils/utils'
import { getFooter } from '../../../monitor-api/modules/commons'
import { createRouteConfig } from '../../router/router-config'
import PerformanceModule from '../../store/modules/performance'
import AuthorityModal from '../../components/authority/AuthorityModal'
import authorityStore from '../../store/modules/authority'
import SetMenu from './set-menu/set-menu'
import { MANAGE_AUTH as GRAFANA_MANAGE_AUTH } from '../grafana/authority-map'
import Vue from 'vue'
import BkPaasLogin from '@blueking/paas-login'
const { mapMutations } = createNamespacedHelpers('app')
const routerList = createRouteConfig()
export default {
  name: 'MonitorNavigation',
  components: {
    LogVersion,
    AuthorityModal,
    SetMenu,
    BkPaasLogin
  },
  mixins: [LogVersionMixin, documentLinkMixin],
  data() {
    return {
      nav: {
        list: routerList,
        id: 'home',
        toggle: false,
        submenuActive: false,
        title: this.$t('监控平台'),
        toggleSet: false
      },
      header: {
        select: {
          list: [],
          value: 0
        },
        needMenu: true,
        setDashboard: false
      },
      user: {
        list: [
          this.$t('项目管理'),
          this.$t('权限中心'),
          this.$t('退出')
        ]
      },
      loading: false,
      // 帮助列表
      help: {
        list: [
          {
            id: 'DOCS',
            name: this.$t('产品文档'),
            href: ''
          },
          {
            id: 'VERSION',
            name: this.$t('版本日志')
          },
          {
            id: 'FAQ',
            name: this.$t('问题反馈'),
            href: window.ce_url
          }
        ]
      },
      // 显示版本日志
      log: {
        show: false
      },
      footer: {
        html: ''
      },
      grafanaMenuList: [
        {
          id: 'create',
          name: this.$t('新建仪表盘')
        },
        {
          id: 'folder',
          name: this.$t('新建目录')
        },
        {
          id: 'import',
          name: this.$t('导入仪表盘')
        }
      ]
    }
  },
  computed: {
    defaultRouteId() {
      return this.$store.getters.navId
    },
    userName() {
      return this.$store.getters.userName || window.uin
    },
    navTitle() {
      return this.$store.getters.navTitle || this.$route.meta.title || ''
    },
    mcMainLoading() {
      return this.$store.getters.mcMainLoading
    },
    showCopyBtn() {
      return [
        'performance',
        'performance-detail',
        'event-center-detail',
        'strategy-config-detail',
        'collect-config-view'
      ].includes(this.$route.name)
    },
    siteUrl() {
      return this.$store.getters.siteUrl || window.site_url || '/'
    },
    enableGrafana() {
      return !!window.enable_grafana
    },
    setDashboardButtonStatus() {
      return this.$store.getters['grafana/setDashboardButtonStatus']
    },
    customContent() {
      return this.$route.meta.customContent
    },
    hasDemoBiz() {
      return this.$store.getters.bizList.some(item => item.is_demo)
    },
    hasDashboardAuth() {
      return this.$store.getters['grafana/hasManageAuth']
    }
  },
  watch: {
    '$route.name': {
      async handler(v) {
        if (v === 'home' && !this.footer.html) {
          this.footer.html = await getFooter().catch(() => '')
        }
      },
      imediadate: true
    }
  },
  beforeCreate() {
    const siteUrl = window.site_url || window.siteUrl
    siteUrl && siteUrl.length > 10 && deleteCookie('bk_biz_id', siteUrl.slice(0, siteUrl.length - 1))
  },
  async created() {
    this.handleGlobalBiz()
    this.handleSetNeedMenu()
    this.nav.toggle = localStorage.getItem('navigationToogle') === 'true'
    this.nav.toggleSet = this.nav.toggle
    Vue.prototype.$authorityStore = authorityStore
  },
  mounted() {
    window.addEventListener('blur', this.handleWindowBlur)
    window.LoginModal = this.$refs.login
  },
  beforeDestroy() {
    window.removeEventListener('blur', this.handleWindowBlur)
  },
  methods: {
    ...mapMutations([SET_BIZ_ID]),
    // 设置是否需要menu
    handleSetNeedMenu() {
      const needMenu = getUrlParam('needMenu')
      this.header.needMenu = `${needMenu}` !== 'false'
    },
    // 设置全局业务
    handleGlobalBiz() {
      const bizId = +getUrlParam('bizId') || +window.cc_biz_id
      this.header.select.value = bizId
      this.header.select.list = this.$store.getters.bizList
    },
    getNavHref(item) {
      if (item.href) {
        return `${this.siteUrl}?bizId=${this.$store.getters.bizId}${item.href}`
      }
      return ''
    },
    async handleNavItemClick(item) {
      // const { bizList, bizId } = this.$store.getters
      // if ((+bizId === - 1 || !(bizList || []).some(item => +item.id === +bizId))) {
      //   return
      // }
      if (this.$route.name !== item.id) {
        await this.$nextTick()
        if (!this.$router.history.pending) {
          this.$router.push({
            name: item.id
          })
        }
      }
    },
    handleCopyLink() {
      const str = `${window.location.origin + window.location.pathname}`
      const url = `${str}?bizId=${this.$store.getters.bizId}${location.hash}${PerformanceModule.urlQuery}`
      copyText(url, (err) => {
        this.$bkMessage('error', err)
      })
      this.$bkMessage({ theme: 'success', message: this.$t('链接复制成功') })
    },
    handleToggle(v) {
      this.nav.toggle = v
    },
    handleToggleClick(v) {
      this.nav.toggleSet = v
      localStorage.setItem('navigationToogle', v)
      this.$store.commit('app/setNavToggle', v)
    },
    handleBizChange(v) {
      window.cc_biz_id = +v
      window.bk_biz_id = +v
      localStorage.setItem('__biz_id__', +v)
      this.$store.commit('app/SET_BIZ_ID', +v)
      console.info(this.$store.getters.bizId, '+++++')
      const { navId } = this.$route.meta
      // 所有页面的子路由在切换业务的时候都统一返回到父级页面
      if (navId !== this.$route.name) {
        const parentRoute = this.$router.options.routes.find(item => item.name === navId)
        if (parentRoute) {
          location.href = `${location.origin}${location.pathname}?bizId=${window.cc_biz_id}#${parentRoute.path}`
        } else {
          this.handleReload()
        }
      } else {
        this.handleReload()
      }
    },
    handleGotoDemo() {
      const demo = this.$store.getters.bizList.find(item => item.is_demo)
      if (demo?.id) {
        if (+this.$store.getters.bizId === +demo.id) {
          location.reload()
        } else {
          this.handleBizChange(demo.id)
        }
      }
    },
    handleReload() {
      const { needClearQuery } = this.$route.meta
      // 清空query查询条件
      if (needClearQuery) {
        location.href = `${location.origin}${location.pathname}?bizId=${window.cc_biz_id}#${this.$route.path}`
      } else {
        location.search = `?bizId=${window.cc_biz_id}`
      }
    },
    handleBack() {
      this.$router.back()
    },
    handleBeforeNavChange(newId, oldId) {
      if ([
        'strategy-config-add',
        'strategy-config-edit',
        'strategy-config-target',
        'alarm-shield-add',
        'alarm-shield-edit',
        'plugin-add',
        'plugin-edit'
      ].includes(this.$route.name)) {
        if (newId !== oldId) {
          this.$router.push({
            name: newId
          })
        }
        return false
      }
      return true
    },
    /**
     * 当前window失去焦点的时候触发
     * 解决 popover不能捕获到iframe的点击事件的问题
     */
    handleWindowBlur() {
      const { headerSelect, setMenu } = this.$refs
      if (headerSelect?.$refs.selectDropdown?.instance) {
        headerSelect.$refs.selectDropdown.instance.hide()
      }
      if (setMenu?.instance) {
        setMenu.instance.hide()
      }
    },
    /**
     * 帮助列表
     */
    handleHelp(item) {
      switch (item.id) {
        case 'DOCS':
          this.handleGotoLink('homeLink')
          break
        case 'FAQ':
          item.href && window.open(item.href)
          break
        case 'VERSION':
          this.log.show = true
          break
      }
    },
    async handleSetDefaultDashboardId() {
      this.header.setDashboard = true
      const success = await this.$store.dispatch('grafana/setDefaultDashboard')
      success && this.$bkMessage({
        message: this.$t('设置成功'),
        theme: 'success'
      })
      this.header.setDashboard = false
    },
    async handleGetBizAuth() {
      const data = await authorityStore.handleGetAuthDetail('view_home')
      if (!data.apply_url) return
      try {
        if (self === top) {
          window.open(data.apply_url, '__blank')
        } else {
          top.BLUEKING.api.open_app_by_other('bk_iam', data.apply_url)
        }
      } catch (_) {
        // 防止跨域问题
        window.open(data.apply_url, '__blank')
      }
    },
    handleGrafanaMenuClick({ id }) {
      this.$store.commit('grafana/setDashboardCheck', `${id}-${Date.now()}`)
    },
    // 无grafana管理权限时触发
    handleUnDashboardAuth() {
      authorityStore.getAuthorityDetail(GRAFANA_MANAGE_AUTH)
    }
  }
}
</script>

<style lang="scss" scoped>
@mixin defualt-icon-mixin($color: #768197) {
  color: $color;
  font-size: 16px;
  position: relative;
  height: 32px;
  width: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 8px;
}
@mixin is-left-mixin($needBgColor: true) {
  color: #63656e;
  &:hover {
    color: #3a84ff;

    @if $needBgColor {
      background: #f0f1f5;
    }
  }
}
@mixin icon-hover-mixin {
  background: linear-gradient(270deg,rgba(37,48,71,1) 0%,rgba(38,50,71,1) 100%);
  border-radius: 100%;
  cursor: pointer;
  color: #d3d9e4;
}
@mixin popover-panel-mxin ($width: 150px, $itemHoverColor: #3A84FF) {
  width: $width;
  display: flex;
  flex-direction: column;
  background: #fff;
  border: 1px solid #e2e2e2;
  box-shadow: 0px 3px 4px 0px rgba(64,112,203,.06);
  padding: 6px 0;
  margin: 0;
  color: #63656e;
  .nav-item {
    flex: 0 0 32px;
    display: flex;
    align-items: center;
    padding: 0 20px;
    list-style: none;
    &:hover {
      color: $itemHoverColor;
      cursor: pointer;
      background-color: #f0f1f5;
    }
  }
}

.monitor-navigation {
  /deep/ .navigation-nav {
    z-index: 9999;
  }
  .custom-content {
    /deep/ .container-content {
      padding: 0;
    }
  }
  .no-need-menu {
    /deep/ .container-header {
      /* stylelint-disable-next-line declaration-no-important */
      display: none !important;
    }
    /deep/ .navigation-container {
      /* stylelint-disable-next-line declaration-no-important */
      max-width: 100vw !important;
    }
    /deep/ .container-content {
      /* stylelint-disable-next-line declaration-no-important */
      max-height: 100vh !important;
    }
  }
  /deep/ .navigation-bar-nav {
    z-index: 1001;
  }
  &.event-center-nav {
    /deep/ .container-content {
      overflow: hidden;
    }
  }
  &.plugin-detail-nav,
  &.uptime-check-nav {
    /deep/ .container-header {
      border-bottom: 0;
      box-shadow: none;
    }
  }
  &.data-retrieval-nav {
    /deep/ .container-content {
      padding: 0;
    }
  }
  &.escalation-content {
    /deep/ .container-content {
      overflow: hidden;
    }
    /deep/ .container-header {
      border-bottom: 0;
      box-shadow: none;
    }
  }
  .monitor-copy-link {
    cursor: pointer;
    margin-left: 10px;
    &:hover {
      color: #3a84ff;
    }
  }
  .set-default {
    margin-left: 20px;
  }
  .monitor-logo {
    width: 32px;
    height: 32px;
  }
  .monitor-menu {
    /deep/ .menu-icon {
      font-size: 18px;
    }
  }
  .monitor-main-loading {
    /* stylelint-disable-next-line declaration-no-important */
    position: absolute !important;
    margin-left: -24px;
    margin-top: -20px;
    width: 100%;
    height: calc(100vh - 52px);
  }
  .help-icon {
    height: 16px;
  }
  &-header {
    flex: 1;
    height: 100%;
    display: flex;
    align-items: center;
    font-size: 14px;
    .header-title {
      margin-right: auto;
      display: flex;
      align-items: center;
      height: 21px;
      font-size: 16px;
      color: #313238;
      line-height: 21px;
      &-back {
        color: #3a84ff;
        font-size: 28px;
        margin-left: -7px;
        cursor: pointer;
      }
    }
    .header-select {
      width: 240px;
      margin-left: auto;
      margin-right: 34px;
      border: 0;
      background: #f0f1f5;
      color: #63656e;
      box-shadow: none;
    }
    .header-mind {
      @include defualt-icon-mixin;
      &.is-left {
        @include is-left-mixin;
      }
      &-mark {
        position: absolute;
        right: 8px;
        top: 8px;
        height: 7px;
        width: 7px;
        border: 1px solid #27334c;
        background-color: #ea3636;
        border-radius: 100%;
        &.is-left {
          border-color: #f0f1f5;
        }
      }
      &:hover {
        @include icon-hover-mixin;
      }
    }
    .header-help {
      @include defualt-icon-mixin;
      &.is-left {
        @include is-left-mixin;
      }
      &:hover {
        @include icon-hover-mixin;
      }
    }
    .header-user {
      height: 100%;
      display: flex;
      align-items: center;
      justify-content: center;
      color: #96a2b9;
      margin-left: 8px;
      .bk-icon {
        margin-left: 5px;
        font-size: 12px;
      }
      &.is-left {
        @include is-left-mixin(false);
      }
      &:hover {
        cursor: pointer;
        color: #d3d9e4;
      }
    }
  }
  &-help {
    @include popover-panel-mxin(170px #63656E);
  }
  &-admin {
    @include popover-panel-mxin(170px #63656E);
  }
  /deep/ .monitor-navigation-footer {
    height: 52px;
    width: 100%;
    margin: 32px 0 0 ;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    border-top: 1px solid #dcdee5;
    color: #63656e;
    font-size: 12px;
    .footer-link {
      margin-bottom: 6px;
      color: #3480fe;
      a {
        color: #3480fe;
        cursor: pointer;
        margin: 0 2px;
      }
    }
  }
}
.select-extension {
  display: flex;
  height: 32px;
  align-items: center;
  margin: 0 -16px;
  &:hover {
    /* stylelint-disable-next-line declaration-no-important */
    background: white !important;
  }
  &-btn {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    &.has-border {
      border-right: 1px solid #eff5ff;
    }
    &:hover {
      cursor: pointer;
      color: #3a84ff;
      background: #eff5ff;
    }
  }
}
</style>
