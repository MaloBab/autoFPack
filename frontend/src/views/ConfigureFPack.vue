<script setup>
import { ref, onMounted } from 'vue'
import ConfigureFPackTable from '../components/ConfigureFPackTable.vue'

</script>

<template>
    <ConfigureFPackTable :fpackId="fpackId" />
</template>