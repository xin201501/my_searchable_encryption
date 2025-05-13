mod crypto;
mod recover_secret;
use actix_web::{HttpResponse, Responder, web};
use base64::prelude::*;
use crypto::symmetric_decryption_for_keyword_128bit;
use crypto::symmetric_decryption_for_keyword_256bit;
use serde::{Deserialize, Serialize};
fn sort_enc_result(
    enc_result_list: Vec<(Vec<u8>, Vec<u8>)>,
    index_key: &[u8],
) -> Result<Vec<(i32, i32)>, String> {
    let symmetric_decryption_for_keyword = if index_key.len() == 16 {
        symmetric_decryption_for_keyword_128bit
    } else if index_key.len() == 32 {
        symmetric_decryption_for_keyword_256bit
    } else {
        return Err("Invalid index key length".to_string());
    };
    let mut plain_result_list = Vec::new();
    for (enc_tf, enc_doc_id) in enc_result_list {
        let plain_tf_str = symmetric_decryption_for_keyword(index_key, &enc_tf)?;

        let plain_doc_id_str = symmetric_decryption_for_keyword(index_key, &enc_doc_id)?;

        let plain_tf: i32 = plain_tf_str
            .parse()
            .map_err(|_| "Invalid TF format".to_string())?;

        let plain_doc_id: i32 = plain_doc_id_str
            .parse()
            .map_err(|_| "Invalid DocID format".to_string())?;

        plain_result_list.push((plain_tf, plain_doc_id));
    }
    // Sort the plain_result_list in descending order by TF
    plain_result_list.sort_by(|a, b| b.0.cmp(&a.0));
    Ok(plain_result_list)
}

#[derive(Debug, Deserialize)]
pub struct SortRequest {
    encrypted_results: Vec<(String, String)>,
    index_key: String,
}

#[derive(Serialize)]
struct SortResponse {
    sorted_results: Vec<(i32, i32)>,
}

#[actix_web::post("/sort-encrypted-results")]
pub async fn sort_encrypted_results(item: web::Json<SortRequest>) -> impl Responder {
    let decoded_results: Result<Vec<_>, _> = item
        .encrypted_results
        .iter()
        .map(|(count_b64, doc_id_b64)| {
            BASE64_STANDARD.decode(count_b64).and_then(|count| {
                BASE64_STANDARD
                    .decode(doc_id_b64)
                    .map(|doc_id| (count, doc_id))
            })
        })
        .collect();

    let decoded_index_key = BASE64_STANDARD.decode(&item.index_key);

    match (decoded_results, decoded_index_key) {
        (Ok(results), Ok(key)) => match sort_enc_result(results, &key) {
            Ok(sorted) => HttpResponse::Ok().json(SortResponse {
                sorted_results: sorted,
            }),
            Err(e) => HttpResponse::BadRequest().body(e),
        },
        _ => HttpResponse::BadRequest().body("Base64 decoding failed"),
    }
}
