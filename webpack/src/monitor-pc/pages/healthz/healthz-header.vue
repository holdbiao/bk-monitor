<template>
  <div class="pattern" style="margin-bottom: 15px">
    <a @click="$emit('update:msg', 0)" :class="msg === 0 ? 'list' : 'error-btn'"> {{ $t('服务状态') }} </a>
    <a v-if="isAdmin" @click="$emit('update:msg', 1)" :class="msg === 1 ? 'list' : 'error-btn'"> {{ $t('异常告警') }} </a>
  </div>
</template>
<script>

export default {
  name: 'MoHealthzHeaderView',
  props: {
    msg: {
      type: Number
    }
  },
  data() {
    return {
      isAdmin: process.env.NODE_ENV === 'development' ? window.is_superuser : window.userInfo.isSuperuser
    }
  },
  methods: {}
}
</script>
<style scoped>
  .pattern {
    width: 100%;
    height: 48px;
    background: #e8eaec;
    font-size: 0;
    padding-top: 4px
  }
  .list {
    display: inline-block;
    width: 120px;
    height: 40px;
    line-height: 40px;
    border-radius: 2px;
    font-size: 14px;
    text-align: center;
    background: #86b1ff;
    color: #fff
  }
  .error-btn {
    display: inline-block;
    width: 120px;
    height: 40px;
    line-height: 40px;
    border-radius: 2px;
    text-align: center;
    background: #fff;
    color: #666;
    font-size: 14px;
  }
</style>
