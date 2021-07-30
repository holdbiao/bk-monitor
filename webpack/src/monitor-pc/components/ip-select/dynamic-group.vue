<template>
    <div> {{ $t('动态分组') }} </div>
</template>
<script>
    export default {
        name: 'dynamic-group',
        props: {
            defaultData: {
                type: Object,
                required: true
            }
        }
    }
</script>
<style lang="scss" scoped>

</style>
