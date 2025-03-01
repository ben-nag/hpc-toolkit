/**
 * Copyright 2023 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

locals {
  # This label allows for billing report tracking based on module.
  labels = merge(var.labels, { ghpc_module = "schedmd-slurm-gcp-v5-login", ghpc_role = "scheduler" })
}

locals {
  ghpc_startup_script = [{
    filename = "ghpc_startup.sh"
    content  = var.startup_script
  }]
  # Since deployment name may be used to create a cluster name, we remove any invalid character from the beginning
  # Also, slurm imposed a lot of restrictions to this name, so we format it to an acceptable string
  tmp_cluster_name   = substr(replace(lower(var.deployment_name), "/^[^a-z]*|[^a-z0-9]/", ""), 0, 10)
  slurm_cluster_name = var.slurm_cluster_name != null ? var.slurm_cluster_name : local.tmp_cluster_name

  enable_public_ip_access_config = var.disable_login_public_ips ? [] : [{ nat_ip = null, network_tier = null }]
  access_config                  = length(var.access_config) == 0 ? local.enable_public_ip_access_config : var.access_config

  additional_disks = [
    for ad in var.additional_disks : {
      disk_name    = ad.disk_name
      device_name  = ad.device_name
      disk_type    = ad.disk_type
      disk_size_gb = ad.disk_size_gb
      disk_labels  = merge(ad.disk_labels, local.labels)
      auto_delete  = ad.auto_delete
      boot         = ad.boot
    }
  ]
}

data "google_compute_default_service_account" "default" {
  project = var.project_id
}

module "slurm_login_template" {
  source = "github.com/SchedMD/slurm-gcp.git//terraform/slurm_cluster/modules/slurm_instance_template?ref=5.9.1"

  additional_disks         = local.additional_disks
  can_ip_forward           = var.can_ip_forward
  slurm_cluster_name       = local.slurm_cluster_name
  disable_smt              = var.disable_smt
  disk_auto_delete         = var.disk_auto_delete
  disk_labels              = merge(var.disk_labels, local.labels)
  disk_size_gb             = var.disk_size_gb
  disk_type                = var.disk_type
  enable_confidential_vm   = var.enable_confidential_vm
  enable_oslogin           = var.enable_oslogin
  enable_shielded_vm       = var.enable_shielded_vm
  gpu                      = one(local.guest_accelerator)
  labels                   = local.labels
  machine_type             = var.machine_type
  metadata                 = var.metadata
  min_cpu_platform         = var.min_cpu_platform
  on_host_maintenance      = var.on_host_maintenance
  preemptible              = var.preemptible
  project_id               = var.project_id
  region                   = var.region
  shielded_instance_config = var.shielded_instance_config
  slurm_instance_role      = "login"
  source_image_family      = local.source_image_family             # requires source_image_logic.tf
  source_image_project     = local.source_image_project_normalized # requires source_image_logic.tf
  source_image             = local.source_image                    # requires source_image_logic.tf
  network                  = var.network_self_link == null ? "" : var.network_self_link
  subnetwork_project       = var.subnetwork_project == null ? "" : var.subnetwork_project
  subnetwork               = var.subnetwork_self_link == null ? "" : var.subnetwork_self_link
  tags                     = concat([local.slurm_cluster_name], var.tags)
  service_account = var.service_account != null ? var.service_account : {
    email  = data.google_compute_default_service_account.default.email
    scopes = ["https://www.googleapis.com/auth/cloud-platform"]
  }
}

module "slurm_login_instance" {
  source = "github.com/SchedMD/slurm-gcp.git//terraform/slurm_cluster/modules/slurm_login_instance?ref=5.9.1"

  access_config         = local.access_config
  slurm_cluster_name    = local.slurm_cluster_name
  instance_template     = var.instance_template != null ? var.instance_template : module.slurm_login_template.self_link
  network               = var.network_self_link
  num_instances         = var.num_instances
  project_id            = var.project_id
  region                = var.region
  static_ips            = var.static_ips
  subnetwork_project    = var.subnetwork_project
  subnetwork            = var.subnetwork_self_link
  zone                  = var.zone
  login_startup_scripts = local.ghpc_startup_script
  metadata              = var.metadata
  slurm_depends_on      = var.controller_instance_id == null ? [] : [var.controller_instance_id]
  enable_reconfigure    = var.enable_reconfigure
  pubsub_topic          = var.pubsub_topic
}
