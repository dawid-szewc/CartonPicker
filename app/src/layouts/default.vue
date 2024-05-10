<template>
  <v-layout class="rounded rounded-md">
    <left-drawer> </left-drawer>
    <app-bar> </app-bar>
    <v-main class="d-flex align-center justify-center" style="min-height: 300px;">
      <router-view> </router-view>
    </v-main>
  </v-layout>
</template>
<script setup>
import LeftDrawer from '@/components/system/LeftDrawer.vue'
import AppBar from '@/components/system/AppBar.vue'
</script>
