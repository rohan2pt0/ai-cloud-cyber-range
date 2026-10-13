# OpenBao on one machine: file storage, plain HTTP on the container network (published to 127.0.0.1 only).
# Lab-grade: ./securax grow sprout initialises it with ONE unseal key kept in ~/.securax/sprout (mode 600), separate
# from the data volume. For real use, switch to cloud-KMS auto-unseal (the canopy stage does) and shamir 3-of-5.
ui            = true
disable_mlock = true
storage "file" {
  path = "/openbao/file"
}
listener "tcp" {
  address     = "0.0.0.0:8200"
  tls_disable = true
}
api_addr = "http://127.0.0.1:8200"
