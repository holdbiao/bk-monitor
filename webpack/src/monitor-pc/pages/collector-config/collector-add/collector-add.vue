<template>
  <div class="collector-add">
    <div class="add-step">
      <ul class="step-list">
        <li class="step-list-item"
            v-for="(item, index) in stepConf.list"
            :key="index"
            :class="[`step-list-item-${index + 1}`, {
              'is-active': stepConf.active === index,
              'is-done': item.done
            }]">
          <div :class="['list-item-content', {
            'is-active-arrow': stepConf.active === index
          }]">
            {{ item.name }}
          </div>
        </li>
      </ul>
    </div>
    <div class="add-container">
      <component @target="target" :hosts.sync="hosts" :is="currentView" :config.sync="config" @previous="handlePrevious" @next="handleNext" :type.sync="componentType"></component>
    </div>
  </div>
</template>

<script>
import ConfigSet from './config-set/config-set'
import ConfigSelect from './config-select/config-select'
import ConfigDelivery from './config-delivery/config-delivery'
import ConfigDone from './config-done/config-done'
import { SET_INFO_DATA } from '../../../store/modules/collector-config'
import authorityMixinCreate from '../../../mixins/authorityMixin'
import * as collectAuth from '../authority-map'
import { createNamespacedHelpers } from 'vuex'
const { mapGetters, mapMutations } = createNamespacedHelpers('collector-config')
export default {
  name: 'CollectorAdd',
  components: {
    ConfigSet,
    ConfigSelect,
    ConfigDelivery,
    ConfigDone
  },
  mixins: [authorityMixinCreate(collectAuth)],
  provide() {
    return {
      authority: this.authority,
      handleShowAuthorityDetail: this.handleShowAuthorityDetail,
      collectAuth
    }
  },
  data() {
    return {
      componentType: 'ADD',
      currentView: 'config-set',
      hosts: {},
      stepConf: {
        active: 0,
        list: [
          {
            name: this.$t('配置'),
            done: false,
            component: 'config-set'
          },
          {
            name: this.$t('选择目标'),
            done: false,
            component: 'config-select'
          },
          {
            name: this.$t('采集下发'),
            done: false,
            component: 'config-delivery'
          },
          {
            name: this.$t('完成'),
            done: false,
            component: 'config-done'
          }
        ]
      },
      config: {
        mode: 'add',
        data: {},
        set: {},
        select: {},
        delivery: {},
        done: {},
        target: {}
      }
    }
  },
  beforeRouteLeave(to, from, next) {
    // 清除新建配置info缓存
    to.name !== 'plugin-add' && this[SET_INFO_DATA](null)
    next()
  },
  computed: {
    ...mapGetters(['addParams'])
  },
  created() {
    const { params } = this.$route
    if (typeof params.id !== 'undefined') {
      this.config = {
        ...this.addParams,
        data: {

          id: params.id,
          updateParams: {
            pluginId: params.pluginId
          }
        },
        mode: 'edit',
        set: {},
        select: {},
        delivery: {},
        done: {},
        target: {}
      }
      this.componentType = 'EDIT'
    }
    this.$store.commit('app/SET_NAV_TITLE', params.id
      ? `${this.$t('route-' + '编辑配置').replace('route-', '')} - #${this.$route.params.id} ${this.$route.params.title}`
      : this.$t('新建配置'))
  },
  methods: {
    ...mapMutations([SET_INFO_DATA]),
    changeView(index) {
      const { stepConf } = this
      this.$set(stepConf, 'active', index)
      this.currentView = stepConf.list[index].component
    },
    handlePrevious() {
      const { stepConf } = this
      const { active } = stepConf
      this.changeView(active - 1)
      stepConf.list[active - 1].done = false
    },
    handleNext() {
      const { stepConf } = this
      const { active } = stepConf
      this.changeView(active + 1)
      stepConf.list[active].done = true
    },
    target(v) {
      this.config.target = v
    }
  }
}
</script>

<style lang="scss" scoped>
  @import "../../home/common/mixins";

  .collector-add {
    min-height: calc(100vh - 80px);
    margin-bottom: -20px;
    display: flex;
    background: #fff;
    border-radius: 2px;
    border: 1px solid #dcdee5;
    border-right: 0;
    .add-step {
      flex: 0 0 202px;
      background: $defaultBgColor;
      border-radius: 2px 0px 0px 0px;
      border-right: 1px solid $defaultBorderColor;
      .step-list {
        margin-left: 45px;
        padding: 40px 0 0 0;

        @for $i from 1 through 4 {
          &-item-#{$i} {
            &:before {
              content: "#{$i}";
            }
          }
        }
        .step-list-item {
          position: relative;
          border-left: 1px dashed $defaultBorderColor;
          height: 70px;
          padding-left: 25px;
          color: $defaultFontColor;
          &:before {
            width: 26px;
            height: 26px;
            line-height: 26px;
            display: inline-block;
            position: absolute;
            border-radius: 50%;
            left: -15px;
            top: -5px;
            text-align: center;
            background: #fff;
            color: $defaultFontColor;

            @include border-1px(#C4C6CC);
          }
          &:last-child {
            border-left: 0;
          }
          .list-item-content {
            position: relative;
            font-size: 14px;
            line-height: 19px;
          }
        }
        .is-active {
          color: $primaryFontColor;

          @include hover();
          &:before {
            color: #fff;
            background: $primaryFontColor;

            @include border-1px($primaryFontColor);
          }
          &-arrow {
            &:after {
              content: "";
              position: absolute;
              right: -6px;
              top: 3px;
              width: 10px;
              height: 10px;
              border-left: 1px solid $defaultBorderColor;
              border-top: 1px solid $defaultBorderColor;
              transform: rotate(-45deg);
              background: #fff;
            }
          }
        }
        .is-done {
          border-left: 1px dashed #dcdee5;

          @include hover();
          &:last-child {
            border-left: 0;
          }
          &:before {
            /* stylelint-disable-next-line declaration-no-important */
            font-size: 28px !important;

            /* stylelint-disable-next-line declaration-no-important */
            content: "\e6b7" !important;

            /* stylelint-disable-next-line declaration-no-important */
            font-family: "icon-monitor" !important;
            background: #dcdee5;
            color: #fff;
            border: 1px solid #dcdee5;
          }
          .list-item-content {
            color: #63656e;
          }
        }
      }
    }
    .add-container {
      flex: 1;
      overflow: auto;
    }
  }
</style>
