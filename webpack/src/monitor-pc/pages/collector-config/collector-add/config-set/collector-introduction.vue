<template>
  <div class="collector-introduction">
    <div class="introduction-header">
      <div class="header-title">
        <div class="title-method" v-if="introduction.type === 'method'"> {{ $t('采集方式介绍') }} </div>
        <div class="title-plugin" v-else> {{ $t('关于') }} {{ introduction.pluginId }} {{ $t('的描述') }} </div>
      </div>
    </div>
    <div class="introduction-content" :style="{ 'padding-left': introduction.type === 'plugin' ? '24px' : '' }">
      <div class="content-desc" v-if="introduction.type === 'plugin'">
        <div class="desc-tag tag-success" v-if="introduction.isOfficial">
          <i class="icon-monitor icon-check-circle tag-icon"></i>
          <span class="tag-text"> {{ $t('官方') }} </span>
        </div>
        <div class="desc-tag tag-warning">
          <i class="icon-monitor tag-icon" :class="[introduction.isSafety ? 'icon-mc-verified-fill' : 'icon-mc-uncertified-fill']"></i>
          <span v-if="introduction.isSafety" class="tag-text"> {{ $t('已认证') }} </span>
          <span v-else class="tag-text"> {{ $t('非认证') }} </span>
        </div>
        <div class="desc-tag"
             v-for="item in introduction.osTypeList"
             :key="item">
          <i :class="['icon-monitor tag-icon', `icon-${item}`]"></i>
          <span class="tag-text">{{ item }}</span>
        </div>
        <div class="desc-tag" v-if="introduction.createUser">
          <i class="icon-monitor icon-user tag-icon"></i>
          <span class="tag-text"> {{ $t('创建者：') }} {{ introduction.createUser }}</span>
        </div>
        <div class="desc-tag" v-if="introduction.updateUser">
          <i class="icon-monitor icon-bianji tag-icon"></i>
          <span class="tag-text"> {{ $t('上次修改者：') }} {{ introduction.updateUser }}</span>
        </div>
      </div>
      <viewer class="content-viewer" :value="introduction.content"></viewer>
    </div>
  </div>
</template>

<script>
import Viewer from '../../../../components/markdown-editor/markdown-viewer'
export default {
  name: 'collector-introduction',
  components: {
    Viewer
  },
  props: {
    introduction: {
      type: Object,
      default: () => ({
        type: 'method',
        content: ''
      })
    }
  }
}
</script>

<style lang="scss" scoped>
  .collector-introduction {
    // width: 400px;
    height: 100vh;
    background: #fafbfd;
    .introduction-header {
      height: 42px;
      background: #f0f1f5;
      border-radius: 0px 0px 1px 1px;
      border-bottom: 1px solid #dcdee5;
      .header-title {
        height: 42px;
        line-height: 42px;
        font-size: 14px;
        .title-method {
          margin-left: 24px;
          font-weight: bold;
          color: #313238;
        }
        .title-plugin {
          margin-left: 24px;
          color: #63656e;
        }
      }
    }
    .introduction-content {
      max-height: calc(100vh - 122px);
      padding: 0 36px 15px 24px;
      overflow: auto;
      .content-desc {
        display: flex;
        align-items: center;
        margin-top: 20px;
        flex-wrap: wrap;
        .desc-tag {
          display: inline-flex;
          align-items: center;
          height: 20px;
          line-height: 18px;
          margin-right: 6px;
          margin-bottom: 5px;
          background: #fff;
          color: #63656e;
          border-radius: 2px;
          border: 1px solid #979ba5;
          .tag-icon {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 20px;
            height: 20px;
            font-size: 14px;
            background: #979ba5;
            color: #fff;
            &.icon-bianji {
              font-size: 20px;
            }
          }
          .tag-text {
            padding: 0 9px;
          }
          &.tag-success {
            border-color: #2dcb56;
            .tag-icon {
              background: #2dcb56;
            }
            .tag-text {
              color: #2dcb56;
            }
          }
          &.tag-warning {
            border-color: #979ba5;
            .tag-icon {
              background: #979ba5;
            }
          }
        }
      }
      .content-viewer {
        /deep/ .tui-editor-contents {
          pre {
            background: #f0f1f5;
          }
        }
      }
    }
  }
</style>
