<template>
  <bk-dialog
    width="768"
    ext-cls="permission-dialog"
    :z-index="2010"
    :mask-close="false"
    :header-position="'left'"
    :title="''"
    @value-change="handleValueChange"
    :value="isModalShow"
    @cancel="onCloseDialog">
    <div class="permission-modal" v-bkloading="{ isLoading: loading }">
      <div class="permission-header">
        <span class="title-icon">
          <img :src="lock" alt="permission-lock" class="lock-img" />
        </span>
        <h3>{{$t('该操作需要以下权限')}}</h3>
      </div>
      <table class="permission-table table-header">
        <thead>
          <tr>
            <!-- <th width="20%">{{$t('系统')}}</th> -->
            <th width="30%">{{$t('需要申请的权限')}}</th>
            <th width="50%">{{$t('关联的资源实例')}}</th>
          </tr>
        </thead>
      </table>
      <div class="table-content">
        <table class="permission-table">
          <tbody>
            <template v-if="authorityDetail.actions && authorityDetail.actions.length > 0">
              <tr v-for="(action, index) in authorityDetail.actions" :key="index">
                <!-- <td width="20%">{{authorityDetail.systemName}}</td> -->
                <td width="30%">{{action.name}}</td>
                <td width="50%">
                  <p
                    class="resource-type-item"
                    v-for="(reItem, reIndex) in getResource(action.relatedResourceTypes)"
                    :key="reIndex">
                    {{reItem}}
                  </p>
                </td>
              </tr>
            </template>
            <tr v-else>
              <td class="no-data" colspan="3">{{$t('无数据')}}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
    <div class="permission-footer" slot="footer">
      <div class="button-group">
        <bk-button theme="primary" @click="goToApply">{{ $t('去申请') }}</bk-button>
        <bk-button theme="default" @click="onCloseDialog">{{ $t('取消') }}</bk-button>
      </div>
    </div>
  </bk-dialog>
</template>
<script lang="ts">
import lockImg from '../../static/images/svg/lock-radius.svg'
import authorityStore from '../../store/modules/authority'
import { Component, Vue, Watch } from 'vue-property-decorator'
@Component
export default class AuthorityModal extends Vue {
  isModalShow = false
  permissionData: any = {}
  lock = lockImg

  get loading() {
    return this.$store.getters['authority/loading']
  }
  get show() {
    return this.$store.getters['authority/showDialog']
  }
  get applyUrl() {
    return this.$store.getters['authority/applyUrl']
  }
  get authorityDetail() {
    return this.$store.getters['authority/authorityDetail']
  }
  @Watch('show')
  onIsModalShowChange(val) {
    this.isModalShow = val
  }
  handleValueChange() {
    authorityStore.setShowAuthortyDialog(this.isModalShow)
  }

  getResource(resoures) {
    if (resoures.length === 0) {
      return ['--']
    }

    const data = []
    resoures.forEach((resource) => {
      if (resource.instances.length > 0) {
        const instances = resource.instances.map(instanceItem => instanceItem.map(item => item.name)
          .join('，')).join('，')
        const resourceItemData = `${resource.typeName}：${instances}`
        data.push(resourceItemData)
      }
    })
    return data
  }
  goToApply() {
    try {
      if (self === top) {
        window.open(this.applyUrl, '__blank')
      } else {
        top.BLUEKING.api.open_app_by_other('bk_iam', this.applyUrl)
      }
    } catch (_) {
      // 防止跨域问题
      window.open(this.applyUrl, '__blank')
    }
  }
  onCloseDialog() {
    this.isModalShow = false
  }
}
</script>
<style lang="scss" scoped>
  .permission-modal {
    .permission-header {
      text-align: center;
      .title-icon {
        display: inline-block;
      }
      .lock-img {
        width: 120px;
      }
      h3 {
        margin: 6px 0 24px;
        color: #63656e;
        font-size: 20px;
        font-weight: normal;
        line-height: 1;
      }
    }
    .permission-table {
      width: 100%;
      color: #63656e;
      border-bottom: 1px solid #e7e8ed;
      border-collapse: collapse;
      table-layout: fixed;
      th,
      td {
        padding: 12px 18px;
        font-size: 12px;
        text-align: left;
        border-bottom: 1px solid #e7e8ed;
        word-break: break-all;
      }
      th {
        color: #313238;
        background: #f5f6fa;
      }
    }
    .table-content {
      max-height: 260px;
      border-bottom: 1px solid #e7e8ed;
      border-top: 0;
      overflow: auto;
      .permission-table {
        border-top: 0;
        border-bottom: 0;
        td:last-child {
          border-right: 0;
        }
        tr:last-child td {
          border-bottom: 0;
        }
        .resource-type-item {
          padding: 0;
          margin: 0;
        }
      }
      .no-data {
        padding: 30px;
        text-align: center;
        color: #999;
      }
    }
  }
  .button-group {
    .bk-button {
      margin-left: 7px;
    }
  }

</style>
