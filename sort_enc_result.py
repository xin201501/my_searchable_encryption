import my


def sort_enc_result(enc_result_list, index_key):
    # 先解密enc_result_list
    plain_result_list = []
    for enc_result in enc_result_list:
        plain_tf_str = my.symmetric_decryption_for_keyword(index_key, enc_result[0])
        plain_doc_id_str = my.symmetric_decryption_for_keyword(index_key, enc_result[1])
        plain_tf = int(plain_tf_str)
        plain_doc_id = int(plain_doc_id_str)
        plain_result = (plain_tf, plain_doc_id)
        plain_result_list.append(plain_result)
        # 对plain_result_list按照tf进行排序
    plain_result_list.sort(key=lambda x: x[0], reverse=True)
    return plain_result_list
