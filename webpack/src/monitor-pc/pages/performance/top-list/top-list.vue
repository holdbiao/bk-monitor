<template>
  <transition name="top-list">
    <ul class="top-list" v-if="list && list.length" v-show="show">
      <li v-for="(item,index) in list" :key="index" class="top-list-item">
        <span class="top-list-item-order">{{index + 1}}</span>
        <span class="top-list-item-name">{{item.name}}</span>
        <span class="top-list-item-status">{{item.percent}}</span>
      </li>
    </ul>
  </transition>
</template>

<script>
export default {
  name: 'top-list',
  props: {
    show: Boolean
  },
  data() {
    return {
      list: [
        {
          name: 'hell1',
          percent: '12%'
        },
        {
          name: 'hell2',
          percent: '12%'
        },
        {
          name: 'hell3',
          percent: '12%'
        },
        {
          name: 'hell4',
          percent: '12%'
        },
        {
          name: 'hell5',
          percent: '12%'
        },
        {
          name: 'hell6',
          percent: '12%'
        },
        {
          name: 'hell7',
          percent: '12%'
        },
        {
          name: 'hell8',
          percent: '12%'
        },
        {
          name: 'hell9',
          percent: '12%'
        },
        {
          name: 'hell10',
          percent: '12%'
        }
      ]
    }
  }
}
</script>

<style scoped lang="scss">
.top-list {
  padding: 6px 16px 4px;
  background: #fff;
  margin: 0;
  display: flex;
  flex-direction: column;
  width: 240px;
  border: 1px solid #dcdee5;
  border-top: 0;
  border-bottom: 0;
  &-item {
    flex: 1 1 24px;
    display: flex;
    flex-direction: row;
    align-items: center;
    justify-content: flex-start;
    font-size: 12px;
    &-order {
      color: #979ba5;
      flex: 0 0 20px;
      text-align: left;
    }
    &-name {
      color: #63656e;
      flex: 1 1 auto;
    }
    &-status {
      color: #2dcb56;
      flex: 0 0 30px;
      text-align: right;
    }
  }
  .top-list-enter-active {
    transition: all .33s cubic-bezier(.23, 1, .32, 1);
  }
  .top-list-enter {
    transform: translate(240px, 0);
  }
  .top-list-leave-active {
    transition: all .33s cubic-bezier(.23, 1, .32, 1);
  }
  .top-list-leave-to {
    transform: translate(250px, 0);
  }
}
</style>
