<template>
  <div class="uptimecheck">
    <uptimecheck-serious v-if="alarm.status === 'serious' || alarm.status === 'slight'" :alarm="alarm"></uptimecheck-serious>
    <common-unset :alarm="alarm" v-else-if="alarm.status === 'unset'"></common-unset>
    <common-noraml :alarm="alarm" v-else-if="alarm.status === 'normal'"></common-noraml>
  </div>
</template>

<script>
import UptimecheckSerious from './uptimecheck-serious'
import CommonUnset from './common-unset'
import CommonNoraml from './common-normal'

export default {
  name: 'uptimecheck',
  components: {
    UptimecheckSerious,
    CommonUnset,
    CommonNoraml
  },
  props: {
    alarm: {
      type: Object,
      default() {
        return {}
      }
    }
  }
}
</script>
