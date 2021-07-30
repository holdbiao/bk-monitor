<template>
  <div class="welcome-page-container">
    <h1 class="title">{{$t('未接入业务或无可查看的业务权限')}}</h1>
    <div class="card-container">
      <div v-if="newBusiness" class="card">
        <img class="card-img" src="../../static/images/svg/new-business.svg" alt="">
        <p class="card-title">{{$t('新业务接入')}}</p>
        <p class="card-detail">{{$t('新业务接入详情')}}</p>
        <bk-button class="common-btn" hover-theme="primary" @click="handleNewBusiness">{{$t('业务接入')}}<i class="icon-monitor icon-mc-wailian"></i></bk-button>
      </div>
      <div v-if="getAccess" class="card">
        <img class="card-img" src="../../static/images/svg/get-access.svg" alt="">
        <p class="card-title">{{$t('获取权限')}}</p>
        <!-- 权限中心带业务ID -->
        <template v-if="getAccess.url && getAccess.businessName">
          <p class="card-detail">{{$t('您当前没有业务') + getAccess.businessName + $t('的权限') + $t('请先申请吧')}}</p>
          <bk-button class="common-btn" theme="primary" @click="handleGetAccess">{{$t('权限申请')}}</bk-button>
        </template>
        <!-- 权限中心不带业务ID -->
        <template v-else-if="getAccess.url && !getAccess.businessName">
          <p class="card-detail">{{$t('您当前没有业务权限，请先申请吧！')}}</p>
          <bk-button class="common-btn" hover-theme="primary" @click="handleGetAccess">{{$t('权限申请')}}</bk-button>
        </template>
        <!-- 未接入权限中心带业务ID -->
        <p v-else-if="getAccess.businessName" class="card-detail">
          {{$t('您当前没有业务') + getAccess.businessName + $t('的权限') + $t('请先联系运维同学') + handleOperator + $t('进行角色的添加')}}
        </p>
        <!-- 未接入权限中心不带业务ID -->
        <p v-else class="card-detail">{{$t('您当前没有业务权限，请先联系对应的业务运维同学进行添加!')}}</p>
      </div>
      <div v-if="demoBusiness && hasDemoBiz" class="card">
        <img class="card-img" src="../../static/images/svg/demo-business.svg" alt="">
        <p class="card-title">{{$t('业务DEMO')}}</p>
        <p class="card-detail">{{$t('您当前想快速体验下平台的功能')}}</p>
        <bk-button class="common-btn" hover-theme="primary" @click="handleDemoBusiness">{{$t('我要体验')}}</bk-button>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import { fetchBusinessInfo } from '../../../monitor-api/modules/commons'
import { Vue, Component } from 'vue-property-decorator'
interface INewBusiness {
  url: string
}
interface IGetAccess {
  url: string, // 权限申请链接（接入权限中心时必填）
  businessName: string, // 业务ID对应的业务名（URL带ID时找到对应业务）
  operator: string[] // 业务ID对应的运维人员ID（没有接入权限中心时URL带ID找到运维人员）
}
@Component({ name: 'NoBusiness' })
export default class NoBusiness extends Vue {
  private newBusiness: INewBusiness =  { url: '' } // 新业务接入链接
  private getAccess: IGetAccess = { url: '',  businessName: '', operator: [] }
  private demoBusiness: INewBusiness = { url: '' } // 业务DEMO链接

  async created() {
    const data = await fetchBusinessInfo().catch(() => false)
    this.newBusiness.url = data.new_biz_apply
    this.getAccess = {
      url: data.get_access_url || '',
      operator: data.operator || [],
      businessName: data.bk_biz_name || ''
    }
  }
  get hasDemoBiz() {
    return this.$store.getters.bizList.some(item => item.is_demo)
  }
  get handleOperator() {
    let str = ''
    const operatorList = this.getAccess.operator
    if (operatorList.length) {
      str = `(${operatorList[0]})`
      if (operatorList[0] === 'admin') {
        str = `(${operatorList[1]})`
      }
    }
    return str
  }
  handleNewBusiness() {
    window.open(this.newBusiness.url)
  }
  handleDemoBusiness() {
    const demo = this.$store.getters.bizList.find(item => item.is_demo)
    if (demo?.id) {
      window.open(`${location.origin}${location.pathname}?bizId=${demo.id}#/`)
    }
  }
  handleGetAccess() {
    window.open(this.getAccess.url)
  }
}
</script>

<style lang="scss" scoped>
  .welcome-page-container {
    display: flow-root;
    height: 100%;
    background: #f4f7fa;
    .title {
      margin: 70px 0 35px;
      height: 26px;
      text-align: center;
      font-size: 20px;
      line-height: 26px;
      color: #313238;
      font-weight: normal;
    }
    .card-container {
      display: flex;
      justify-content: center;
      .card {
        display: flex;
        flex-flow: column;
        align-items: center;
        width: 260px;
        height: 400px;
        background: #fff;
        border-radius: 2px;
        transition: box-shadow .3s;
        &:not(:last-child) {
          margin-right: 40px;
        }
        &:hover {
          transition: box-shadow .3s;
          box-shadow: 0 3px 6px 0 rgba(0, 0, 0, .1);
        }
        .card-img {
          margin: 28px 0 20px;
          width: 220px;
          height: 160px;
        }
        .card-title {
          font-size: 16px;
          font-weight: 500;
          line-height: 22px;
          color: #313238;
        }
        .card-detail {
          display: flex;
          justify-content: center;
          align-items: center;
          width: 200px;
          height: 60px;
          margin: 11px 0 21px;
          text-align: center;
          font-size: 12px;
          line-height: 20px;
          color: #63656e;
        }
        .common-btn {
          width: 200px;
          display: flex;
          align-items: center;
          justify-content: center;
          /deep/ span {
            display: flex;
            align-items: center;
            justify-content: center;
          }
          .icon-monitor {
            font-size: 18px;
            margin-left: 4px;
          }
        }
      }
    }
  }
</style>
