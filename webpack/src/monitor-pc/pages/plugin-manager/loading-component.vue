<template>
  <div v-bkloading="{ isLoading: true }"></div>
</template>
<script>
export default {
  name: 'loading-component'
}
</script>
<style lang="scss" scoped>
div {
  height: 100%;
  width: 100%;
}
</style>
