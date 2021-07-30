<template>
    <svg class="svg-icon" v-bind="$attrs" aria-hidden="true" @click="clickHandle">
        <use :xlink:href="iconId" />
    </svg>
</template>

<script>
    export default {
        name: 'svg-icon',
        props: {
            iconName: {
                type: String,
                required: true
            }
        },
        computed: {
            iconId () {
                if (this.iconName.match(/icon-/)) {
                    return `#${this.iconName.trim().toLocaleString()}`
                }
                return `#icon-${this.iconName.trim().toLocaleString()}`
            }
        },
        methods: {
            clickHandle (e) {
                this.$emit('click', e)
            }
        }
    }
</script>

<style scoped>
    .svg-icon {
        width: 1em;
        height: 1em;
        vertical-align: middle;
        fill: currentColor;
        overflow: hidden;
    }
</style>
