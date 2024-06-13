<template>
  <div>
    <h1>Carton Manager</h1>
    <div v-for="(item, index) in data" :key="index">
      <v-card
        class="mx-auto my-4"
        :elevation=2
        max-width="100%"
        width="1000"
        >
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn
            icon="mdi-file-edit-outline"
            size="small"
            @click="openDialog(item)"
          ></v-btn>
        </v-card-actions>

        <template v-slot:title>
          Number: {{ index }}
        </template>

        <template v-slot:subtitle>
          Description: {{ item.description }}
        </template>

        <template v-slot:text>
          <div v-for="(variant, variant_index) in item.variants" :key="variant_index">
            <v-sheet
              :elevation="4"
              class="mb-1"
              border
              rounded
              >
              <v-chip class="ma-2" color="pink" label>
                variant: {{ variant_index }}
              </v-chip>
              <v-chip class="mr-1" color="pink" label>
                description: {{ variant.description }}
              </v-chip>
              <v-chip class="ma-2" color="pink" label>
                ratio: {{ variant.ratio }}
              </v-chip>
              <v-chip class="ma-2" color="pink" label>
                width: {{ variant.width }}
              </v-chip>
            </v-sheet>
          </div>
        </template>
      </v-card>
      <br>
    </div>

    <!-- Dialog -->
    <v-dialog v-model="dialog" max-width="800">
      <v-card>
        <v-toolbar dark color="primary">
          <v-btn icon dark @click="closeDialog">
            <v-icon>mdi-close</v-icon>
          </v-btn>
          <v-toolbar-title>Edit Item</v-toolbar-title>
          <v-spacer></v-spacer>
        </v-toolbar>
        <v-card-text>
          <v-form>
            <v-text-field v-model="selectedItem.description" label="Description"></v-text-field>
            
            <!-- Variants list -->
             <v-expansion-panels>
              <v-expansion-panel
                v-for="(variant, variantIndex) in selectedItem.variants"
                :key="variantIndex"
                >
                <template v-slot:title>
                  Variant number: {{variantIndex}}
                </template>
                <template v-slot:text>
                    <v-text-field v-model="variant.description" label="Description"></v-text-field>
                    <v-text-field v-model="variant.ratio" label="Ratio"></v-text-field>
                    <v-text-field v-model="variant.width" label="Width"></v-text-field>
                    <v-btn prepend-icon="mdi-delete" block color="error" @click="removeVariant(variantIndex)">
                      delete variant
                    </v-btn>
                </template>
              </v-expansion-panel>
            </v-expansion-panels>           
            <!-- Przyciski do zarządzania wariantami -->
            <v-btn prepend-icon="mdi-plus" block class="mt-4" color="success" @click="addVariant">Add Variant</v-btn>
          </v-form>
        </v-card-text>
        <v-card-actions>
          <v-btn prepend-icon="mdi-content-save-outline" color="success" @click="saveItem">Save</v-btn>
          <v-btn prepend-icon="mdi-delete-outline" color="error" @click="saveItem">Remove</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

const data = ref([])
const dialog = ref(false)
const selectedItem = ref({})

const fetchItems = async () => {
  try {
    const response = await axios.get('http://localhost:8000/api/cardboard_data')
    data.value = response.data.cardboards
  } catch (error) {
    console.error('Error fetching items:', error)
  }
}

const openDialog = (item) => {
  selectedItem.value = { ...item }
  dialog.value = true
}

const closeDialog = () => {
  dialog.value = false
}

const saveItem = () => {
  console.log('Saving item', selectedItem.value)
  // Tutaj dodaj logikę zapisu zmian
  closeDialog()
}

onMounted(fetchItems)
</script>
