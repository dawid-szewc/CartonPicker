<template>
  <v-navigation-drawer>
    <v-list density="compact" nav>
      <RouterLink to="/" class="router-link">
        <v-list-item title="Home"></v-list-item>
      </RouterLink>
      <RouterLink to="/about" class="router-link">
        <v-list-item title="About"></v-list-item>
      </RouterLink>
    </v-list>
  </v-navigation-drawer>
</template>
