import base64
import time
from OpenSSL import crypto
import binascii    
import boto3
import rsa

from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from botocore.signers import CloudFrontSigner
from datetime import datetime

def start(filename, timestamp : int, filetype="audio"):
    """
    Start creating the URL signature

    :param filename str
    :param timestamp int - when the file was created
    :param filetype string
    :return str
    """
    key_pair_id = 'K2LREIU2NS8IZR'

    # Default for audio files
    expire_time = 60*60*24
    if filetype == "profile_photo":
        # 20 years, (ie, dont expire)
        expire_time = 60*60*24*365*20

    # 24hr from when the file was created
    expires = timestamp + expire_time
    expired_object = datetime.fromtimestamp(expires)
    url = 'https://media.alexpeyton.com/' + filename

    cloudfront_signer = CloudFrontSigner(key_pair_id, rsa_signer)
    
    # Create a signed url that will be valid until the specfic expiry date
    # provided using a canned policy.
    signed_url = cloudfront_signer.generate_presigned_url(
        url, date_less_than=expired_object)
    return signed_url

def rsa_signer(message):
    ssm = boto3.client('ssm', region_name="us-east-2")
    priv_key = ssm.get_parameter(
        Name='CloudFrontPK'
    )

    pk = priv_key['Parameter']['Value'].replace("\\n", "\n").replace("\\t", "\t")
    return rsa.sign(
        message,
        rsa.PrivateKey.load_pkcs1(pk),
        "SHA-1")

def get_canned_policy_stream_name(audio_path, key_pair_id, expires):
    """
    This policy is well known by CloudFront, but you still need to sign it, since it contains your parameters
    
    return string
    """
    canned_policy = '{"Statement":[{"Resource":"' + audio_path + '","Condition":{"DateLessThan":{"AWS:EpochTime":' +  str(expires) + '}}}]}'
    # the policy contains characters that cannot be part of a URL, so we base64 encode it
    encoded_policy = url_safe_base64_encode(canned_policy)
    # sign the original policy, not the encoded version
    signature = rsa_sha1_sign(canned_policy)
    
    # make the signature safe to be included in a URL
    #encoded_signature = url_safe_base64_encode(signature)
    encoded_signature = url_safe_base64_encode(signature)
    
    # combine the above into a stream name
    stream_name = create_stream_name(audio_path, None, encoded_signature, key_pair_id, expires)
    # URL-encode the query string characters to support Flash Player
    return encode_query_params(stream_name)

def create_stream_name(stream, policy, signature, key_pair_id, expires):
    result = stream
    # if the stream already contains query parameters, attach the new query parameters to the end
    # otherwise, add the query parameters
    separator = '?' if not '?' in stream else '&'
    
    # the presence of an expires time means we're using a canned policy
    if expires:
        result += '' + separator + "Expires=" + str(expires) + "&Signature=" + signature + "&Key-Pair-Id=" + key_pair_id
    
    # not using a canned policy, include the policy itself in the stream name
    else:
        result += '' + separator + "Policy=" + policy + "&Signature=" + signature + "&Key-Pair-Id=" + key_pair_id

    # new lines would break us, so remove them
    result = result.replace('\n', '')

    return result

def getCustomPolicy(audio_path, client_ip, expires):
    """
    Get the polcy json string

    :return string
    """
    policy = '{"Statement":[' \
        '{' \
            '"Resource":"' +  audio_path + '",' \
            '"Condition":{' \
                '"IpAddress":{"AWS:SourceIp":"' + client_ip + '/32"},' \
                '"DateLessThan":{"AWS:EpochTime":' + expires + '}' \
            '}' \
        '}' \
    ']}'

    return policy

def rsa_sha1_sign(policy):
    """
    Compute signature of policy with private key
    """
    # load the private key
    #priv_key = ''
    #with open(private_key_filename, "r") as fp:
    #    priv_key = fp.read()

    ssm = boto3.client('ssm', region_name="us-east-2")
    priv_key = ssm.get_parameter(
        Name='CloudFrontPK'
    )

    priv_key = priv_key['Parameter']['Value']
   
    pkeyid = crypto.load_privatekey(crypto.FILETYPE_PEM, priv_key)
    #pkeyid = openssl_get_privatekey(priv_key)

    # compute signature
    # return signature is in binary string
    signature_bin_str = crypto.sign(pkeyid, policy, 'sha1')
    #openssl_sign(policy, signature, pkeyid)
    
    # Convert binary string to hexidecimal
    signature_hex = binascii.hexlify(signature_bin_str)

    # Convert binary to string
    signature = signature_hex.decode("ascii")

    # Convert signature to upper case
    fpx_checksum = str(signature).upper()
    return fpx_checksum


def url_safe_base64_encode(value):
    """
    Base 64 encode the string
    :return str
    """
    encoded = str(base64.b64encode(value.encode("utf-8")).decode('utf-8'))
    #encoded = str(base64.urlsafe_b64encode(value.encode("utf-8")).decode())

    # replace unsafe characters +, = and / with the safe characters -, _ and ~
    encoded = encoded.replace('+','-').replace('=','_').replace('/','~')
    return encoded

def encode_query_params(stream_name):
    """
    Encode the query params

    :return string
    """
    # Adobe Flash Player has trouble with query parameters being passed into it,
    # so replace the bad characters with their URL-encoded forms
    #stream_name = stream_name.replace('?', '%3F')
    #stream_name = stream_name.replace('=', '%3D')
    #stream_name = stream_name.replace('&', '%26')
    return stream_name
